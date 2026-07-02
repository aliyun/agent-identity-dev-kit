package agentidentity

import (
	"context"
	"fmt"
	"time"

	controlclient "github.com/alibabacloud-go/agentidentity-20250901/client"
	dataclient "github.com/alibabacloud-go/agentidentitydata-20251127/client"
	openapi "github.com/alibabacloud-go/darabonba-openapi/v2/client"
	"github.com/alibabacloud-go/tea/tea"
	credential "github.com/aliyun/credentials-go/credentials"
)

// CreateWorkloadIdentityOption configures CreateWorkloadIdentity.
type CreateWorkloadIdentityOption struct {
	WorkloadName                   string
	RoleArn                        string
	AllowedResourceOAuth2ReturnUrls []string
	IdentityProviderName           string
}

// GetWorkloadAccessTokenOption configures GetWorkloadAccessToken.
type GetWorkloadAccessTokenOption struct {
	UserToken string
	UserId    string
}

// ConfirmUserAuthOption configures ConfirmUserAuth.
type ConfirmUserAuthOption struct {
	UserId    string
	UserToken string
}

// GetTokenOptions configures GetToken.
type GetTokenOptions struct {
	ProviderName        string
	AgentIdentityToken  string
	AuthFlow            string
	Scopes              []string
	OnAuthUrl           func(url string)
	CallbackUrl         string
	ForceAuthentication bool
	CustomState         string
	CustomParameters    map[string]string
	Credential          credential.Credential
}

const (
	defaultPollMaxRetries = 60
	defaultPollInterval   = 5 * time.Second
)

// GetApiKeyOptions configures GetApiKey.
type GetApiKeyOptions struct {
	ProviderName       string
	AgentIdentityToken string
	Credential         credential.Credential
}

// AssumeRoleOptions configures AssumeRoleForWorkloadIdentity.
type AssumeRoleOptions struct {
	WorkloadToken   string
	RoleSessionName string
	DurationSeconds int64
	Policy          string
}

// CreateWorkloadIdentity creates a workload identity with the specified parameters.
func (c *IdentityClient) CreateWorkloadIdentity(ctx context.Context, opts ...CreateWorkloadIdentityOption) (string, error) {
	var opt CreateWorkloadIdentityOption
	if len(opts) > 0 {
		opt = opts[0]
	}

	workloadName := opt.WorkloadName
	if workloadName == "" {
		workloadName = "workload-" + generateRandomHex(4)
	}

	request := &controlclient.CreateWorkloadIdentityRequest{
		WorkloadIdentityName:             tea.String(workloadName),
		AllowedResourceOAuth2ReturnURLs:  tea.StringSlice(opt.AllowedResourceOAuth2ReturnUrls),
		RoleArn:                          tea.String(opt.RoleArn),
		IdentityProviderName:             tea.String(opt.IdentityProviderName),
	}

	response, err := c.controlClient.CreateWorkloadIdentity(request)
	if err != nil {
		return "", fmt.Errorf("failed to create workload identity: %w", err)
	}

	return tea.StringValue(response.Body.WorkloadIdentity.WorkloadIdentityName), nil
}

// GetWorkloadAccessToken gets a workload access token.
// Priority: userToken (JWT path) > userId (UserID path) > no user info path.
func (c *IdentityClient) GetWorkloadAccessToken(ctx context.Context, workloadName string, opts ...GetWorkloadAccessTokenOption) (string, error) {
	if workloadName == "" {
		return "", fmt.Errorf("workloadName is required")
	}

	var opt GetWorkloadAccessTokenOption
	if len(opts) > 0 {
		opt = opts[0]
	}

	if opt.UserToken != "" {
		request := &dataclient.GetWorkloadAccessTokenForJWTRequest{
			WorkloadIdentityName: tea.String(workloadName),
			UserToken:            tea.String(opt.UserToken),
		}
		resp, err := c.dataClient.GetWorkloadAccessTokenForJWT(request)
		if err != nil {
			return "", fmt.Errorf("failed to get workload access token (JWT): %w", err)
		}
		return tea.StringValue(resp.Body.WorkloadAccessToken), nil
	} else if opt.UserId != "" {
		request := &dataclient.GetWorkloadAccessTokenForUserIdRequest{
			WorkloadIdentityName: tea.String(workloadName),
			UserId:               tea.String(opt.UserId),
		}
		resp, err := c.dataClient.GetWorkloadAccessTokenForUserId(request)
		if err != nil {
			return "", fmt.Errorf("failed to get workload access token (user ID): %w", err)
		}
		return tea.StringValue(resp.Body.WorkloadAccessToken), nil
	} else {
		request := &dataclient.GetWorkloadAccessTokenRequest{
			WorkloadIdentityName: tea.String(workloadName),
		}
		resp, err := c.dataClient.GetWorkloadAccessToken(request)
		if err != nil {
			return "", fmt.Errorf("failed to get workload access token: %w", err)
		}
		return tea.StringValue(resp.Body.WorkloadAccessToken), nil
	}
}

// ConfirmUserAuth confirms user authentication to complete OAuth2 3LO flow.
func (c *IdentityClient) ConfirmUserAuth(ctx context.Context, sessionUri string, opts ...ConfirmUserAuthOption) error {
	if sessionUri == "" {
		return fmt.Errorf("sessionUri is required")
	}

	var opt ConfirmUserAuthOption
	if len(opts) > 0 {
		opt = opts[0]
	}

	request := &dataclient.CompleteResourceTokenAuthRequest{
		SessionURI: tea.String(sessionUri),
	}
	if opt.UserId != "" || opt.UserToken != "" {
		request.UserIdentifier = &dataclient.CompleteResourceTokenAuthRequestUserIdentifier{
			UserId:  tea.String(opt.UserId),
			UserJWT: tea.String(opt.UserToken),
		}
	}
	_, err := c.dataClient.CompleteResourceTokenAuth(request)
	if err != nil {
		return fmt.Errorf("failed to confirm user auth: %w", err)
	}
	return nil
}

// newDataClientWithCredential creates a data client using the given credential.
func (c *IdentityClient) newDataClientWithCredential(cred credential.Credential) (*dataclient.Client, error) {
	dataEndpoint := c.dataApiEndpoint
	if dataEndpoint == "" {
		dataEndpoint = fmt.Sprintf("agentidentitydata.%s.aliyuncs.com", c.regionId)
	}
	dataConfig := &openapi.Config{
		Credential: cred,
		RegionId:   tea.String(c.regionId),
		Endpoint:   tea.String(dataEndpoint),
	}
	if c.protocol != "" {
		dataConfig.Protocol = tea.String(c.protocol)
	}
	return dataclient.NewClient(dataConfig)
}

// GetToken gets an OAuth2 access token for the specified provider.
func (c *IdentityClient) GetToken(ctx context.Context, opts GetTokenOptions) (string, error) {
	client := c.dataClient

	if c.useSts && opts.Credential != nil {
		var err error
		client, err = c.newDataClientWithCredential(opts.Credential)
		if err != nil {
			return "", fmt.Errorf("failed to create STS data client: %w", err)
		}
	}

	// Convert custom parameters map to map[string]interface{}
	var customParamsMap map[string]interface{}
	if opts.CustomParameters != nil {
		customParamsMap = make(map[string]interface{})
		for k, v := range opts.CustomParameters {
			customParamsMap[k] = tea.String(v)
		}
	}

	request := &dataclient.GetResourceOAuth2TokenRequest{
		ResourceCredentialProviderName: tea.String(opts.ProviderName),
		Scopes:                         tea.StringSlice(opts.Scopes),
		OAuth2Flow:                     tea.String(opts.AuthFlow),
		WorkloadAccessToken:            tea.String(opts.AgentIdentityToken),
		ResourceOAuth2ReturnURL:        tea.String(opts.CallbackUrl),
		ForceAuthentication:            tea.Bool(opts.ForceAuthentication),
		CustomState:                    tea.String(opts.CustomState),
		CustomParameters:               customParamsMap,
	}

	response, err := client.GetResourceOAuth2Token(request)
	if err != nil {
		return "", fmt.Errorf("failed to get OAuth2 token: %w", err)
	}
	responseBody := response.Body

	if tea.StringValue(responseBody.AccessToken) != "" {
		return tea.StringValue(responseBody.AccessToken), nil
	}

	if tea.StringValue(responseBody.AuthorizationURL) != "" {
		if opts.OnAuthUrl != nil {
			opts.OnAuthUrl(tea.StringValue(responseBody.AuthorizationURL))
		}

		pollRequest := *request
		if opts.ForceAuthentication {
			pollRequest.ForceAuthentication = tea.Bool(false)
		}

		if tea.StringValue(responseBody.SessionURI) != "" {
			pollRequest.SessionURI = responseBody.SessionURI
		}

		// Use original data client for polling, matching Python SDK behavior.
		// The STS credential client is only used for the initial GetResourceOAuth2Token call.
		return c.pollForOAuth2Token(ctx, c.dataClient, &pollRequest, defaultPollMaxRetries, defaultPollInterval)
	}

	return "", fmt.Errorf("failed to obtain OAuth2 token for current workload identity: Identity service did not return a token or an authorization URL")
}

// GetApiKey gets an API key from the Identity service.
func (c *IdentityClient) GetApiKey(ctx context.Context, opts GetApiKeyOptions) (string, error) {
	client := c.dataClient

	if c.useSts && opts.Credential != nil {
		var err error
		client, err = c.newDataClientWithCredential(opts.Credential)
		if err != nil {
			return "", fmt.Errorf("failed to create STS data client: %w", err)
		}
	}

	request := &dataclient.GetResourceAPIKeyRequest{
		ResourceCredentialProviderName: tea.String(opts.ProviderName),
		WorkloadAccessToken:            tea.String(opts.AgentIdentityToken),
	}

	response, err := client.GetResourceAPIKey(request)
	if err != nil {
		return "", fmt.Errorf("failed to get API key: %w", err)
	}

	apikey := tea.StringValue(response.Body.APIKey)
	if apikey != "" {
		return apikey, nil
	}
	return "", fmt.Errorf("failed to get API key: Identity service did not return an API key")
}

// AssumeRoleForWorkloadIdentity assumes a role to get STS temporary credentials.
func (c *IdentityClient) AssumeRoleForWorkloadIdentity(ctx context.Context, opts AssumeRoleOptions) (*STSCredential, error) {
	if opts.WorkloadToken == "" {
		return nil, fmt.Errorf("workload token is required")
	}

	durationSeconds := opts.DurationSeconds
	if durationSeconds == 0 {
		durationSeconds = defaultSessionDuration
	}

	request := &dataclient.AssumeRoleForWorkloadIdentityRequest{
		WorkloadAccessToken: tea.String(opts.WorkloadToken),
		RoleSessionName:     tea.String(opts.RoleSessionName),
		DurationSeconds:     tea.String(fmt.Sprintf("%d", durationSeconds)),
	}
	if opts.Policy != "" {
		request.Policy = tea.String(opts.Policy)
	}

	response, err := c.dataClient.AssumeRoleForWorkloadIdentity(request)
	if err != nil {
		return nil, fmt.Errorf("failed to assume role for workload identity: %w", err)
	}

	cred := response.Body.Credentials
	return &STSCredential{
		AccessKeyId:     tea.StringValue(cred.AccessKeyId),
		AccessKeySecret: tea.StringValue(cred.AccessKeySecret),
		SecurityToken:   tea.StringValue(cred.SecurityToken),
		Expiration:      tea.StringValue(cred.Expiration),
	}, nil
}

// GetStsCredentialClient gets a Credential client backed by cached STS credentials.
func (c *IdentityClient) GetStsCredentialClient(ctx context.Context, workloadToken, userId, userToken string) (credential.Credential, error) {
	if workloadToken == "" {
		return nil, fmt.Errorf("workloadToken is required")
	}

	cacheKey := getStsCacheKey(workloadToken, userId, userToken)
	cachedCredential := GetCachedCredential(cacheKey)
	if cachedCredential != nil {
		return convertToCredential(cachedCredential)
	}

	stsCredential, err := c.AssumeRoleForWorkloadIdentity(ctx, AssumeRoleOptions{
		WorkloadToken:   workloadToken,
		RoleSessionName: fmt.Sprintf("AgentIdentitySessionRole-%s", generateUUID()),
	})
	if err != nil {
		return nil, err
	}

	StoreCredentialInCache(cacheKey, stsCredential)
	return convertToCredential(stsCredential)
}

// convertToCredential converts an STSCredential to a credentials-go Credential instance.
func convertToCredential(stsCred *STSCredential) (credential.Credential, error) {
	config := new(credential.Config).
		SetType("sts").
		SetAccessKeyId(stsCred.AccessKeyId).
		SetAccessKeySecret(stsCred.AccessKeySecret).
		SetSecurityToken(stsCred.SecurityToken)

	return credential.NewCredential(config)
}

// pollForOAuth2Token polls for an OAuth2 token until obtained or max retries reached.
// Context cancellation is respected at the poll loop level.
func (c *IdentityClient) pollForOAuth2Token(
	ctx context.Context,
	client *dataclient.Client,
	request *dataclient.GetResourceOAuth2TokenRequest,
	maxRetries int,
	delay time.Duration,
) (string, error) {
	var lastErr error
	for attempt := 0; attempt < maxRetries; attempt++ {
		response, err := client.GetResourceOAuth2Token(request)
		if err != nil {
			lastErr = err
		} else {
			accessToken := tea.StringValue(response.Body.AccessToken)
			if accessToken != "" {
				return accessToken, nil
			}
			lastErr = nil
		}

		if attempt < maxRetries-1 {
			select {
			case <-ctx.Done():
				return "", ctx.Err()
			case <-time.After(delay):
				// Continue polling
			}
		}
	}

	if lastErr != nil {
		return "", fmt.Errorf("failed to get OAuth2 token after %d attempts: %w", maxRetries, lastErr)
	}
	return "", fmt.Errorf("failed to get OAuth2 token after %d attempts", maxRetries)
}
