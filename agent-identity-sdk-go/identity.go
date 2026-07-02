package agentidentity

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"os"

	controlclient "github.com/alibabacloud-go/agentidentity-20250901/client"
	dataclient "github.com/alibabacloud-go/agentidentitydata-20251127/client"
	openapi "github.com/alibabacloud-go/darabonba-openapi/v2/client"
	"github.com/alibabacloud-go/tea/tea"
	credential "github.com/aliyun/credentials-go/credentials"
)

const (
	defaultSessionDuration = 3600 // 1 hour, per RAM AssumeRole limits
)

// IdentityClient is the core struct of the Agent Identity SDK.
// It wraps the Alibaba Cloud Agent Identity control plane and data plane APIs.
type IdentityClient struct {
	regionId           string
	useSts             bool
	protocol           string
	credential         credential.Credential
	controlClient      *controlclient.Client
	dataClient         *dataclient.Client
	dataApiEndpoint    string
	controlApiEndpoint string
}

// Option is a function that configures an IdentityClient.
type Option func(*IdentityClient)

// WithDataApiEndpoint sets a custom data plane API endpoint.
func WithDataApiEndpoint(endpoint string) Option {
	return func(c *IdentityClient) {
		c.dataApiEndpoint = endpoint
	}
}

// WithControlApiEndpoint sets a custom control plane API endpoint.
func WithControlApiEndpoint(endpoint string) Option {
	return func(c *IdentityClient) {
		c.controlApiEndpoint = endpoint
	}
}

// WithProtocol sets the protocol for API calls (e.g. "HTTP", "HTTPS").
func WithProtocol(protocol string) Option {
	return func(c *IdentityClient) {
		c.protocol = protocol
	}
}

// NewIdentityClient creates a new IdentityClient.
func NewIdentityClient(regionId string, opts ...Option) (*IdentityClient, error) {
	if regionId == "" {
		return nil, fmt.Errorf("regionId is required")
	}
	client := &IdentityClient{
		regionId: regionId,
	}

	// Apply options
	for _, opt := range opts {
		opt(client)
	}

	// Read STS mode from environment variable, default true
	useStsEnv := os.Getenv("AGENT_IDENTITY_USE_STS")
	if useStsEnv == "" {
		client.useSts = true
	} else {
		client.useSts = useStsEnv == "true"
	}

	// Initialize credential using default credential chain
	cred, err := credential.NewCredential(nil)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize credentials: %w", err)
	}
	client.credential = cred

	// Build endpoints
	controlEndpoint := client.controlApiEndpoint
	if controlEndpoint == "" {
		controlEndpoint = fmt.Sprintf("agentidentity.%s.aliyuncs.com", regionId)
	}
	dataEndpoint := client.dataApiEndpoint
	if dataEndpoint == "" {
		dataEndpoint = fmt.Sprintf("agentidentitydata.%s.aliyuncs.com", regionId)
	}

	// Create control plane client
	controlConfig := &openapi.Config{
		Credential: client.credential,
		RegionId:   tea.String(regionId),
		Endpoint:   tea.String(controlEndpoint),
	}
	if client.protocol != "" {
		controlConfig.Protocol = tea.String(client.protocol)
	}
	cc, err := controlclient.NewClient(controlConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create control client: %w", err)
	}
	client.controlClient = cc

	// Create data plane client
	dataConfig := &openapi.Config{
		Credential: client.credential,
		RegionId:   tea.String(regionId),
		Endpoint:   tea.String(dataEndpoint),
	}
	if client.protocol != "" {
		dataConfig.Protocol = tea.String(client.protocol)
	}
	dc, err := dataclient.NewClient(dataConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create data client: %w", err)
	}
	client.dataClient = dc

	return client, nil
}

// getStsCacheKey generates a cache key for STS credential caching.
func getStsCacheKey(userId, idToken, roleSessionName string) string {
	return fmt.Sprintf("%s:%s:%s", userId, idToken, roleSessionName)
}

// generateRandomHex generates a random hex string of the specified byte length.
func generateRandomHex(n int) string {
	bytes := make([]byte, n)
	if _, err := rand.Read(bytes); err != nil {
		panic(fmt.Sprintf("rand.Read failed: %v", err))
	}
	return hex.EncodeToString(bytes)
}

// generateUUID generates a UUID v4 string.
func generateUUID() string {
	bytes := make([]byte, 16)
	if _, err := rand.Read(bytes); err != nil {
		panic(fmt.Sprintf("rand.Read failed: %v", err))
	}
	bytes[6] = (bytes[6] & 0x0f) | 0x40 // Version 4
	bytes[8] = (bytes[8] & 0x3f) | 0x80 // Variant 10
	return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x",
		bytes[0:4], bytes[4:6], bytes[6:8], bytes[8:10], bytes[10:16])
}
