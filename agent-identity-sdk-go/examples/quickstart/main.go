package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"sync"
	"time"

	agentidentity "github.com/aliyun/agent-identity-dev-kit/agent-identity-sdk-go"
)

// Usage:
//
//	# Get STS credential (default)
//	go run main.go
//
//	# Get API key
//	go run main.go apikey <provider-name>
//
//	# Get OAuth2 token
//	go run main.go oauth <provider-name>
//
//	# Get all three
//	go run main.go all <provider-name>
func main() {
	args := os.Args[1:]

	// Parse command: [cmd] [provider-name]
	cmd := "sts"
	provider := ""
	if len(args) > 0 {
		cmd = args[0]
	}
	if len(args) > 1 {
		provider = args[1]
	}

	if cmd != "sts" && cmd != "apikey" && cmd != "oauth" && cmd != "all" {
		fmt.Fprintf(os.Stderr, "Usage: %s [sts|apikey|oauth|all] [provider-name]\n", os.Args[0])
		os.Exit(1)
	}
	if cmd != "sts" && provider == "" {
		fmt.Fprintf(os.Stderr, "Usage: %s %s <provider-name>\n", os.Args[0], cmd)
		os.Exit(1)
	}

	ctx := context.Background()

	// Apply user identity from environment variables.
	userId := os.Getenv("AGENT_IDENTITY_USER_ID")
	userToken := os.Getenv("AGENT_IDENTITY_USER_TOKEN")
	if userId != "" {
		ctx = agentidentity.WithUserId(ctx, userId)
	}
	if userToken != "" {
		ctx = agentidentity.WithUserToken(ctx, userToken)
	}

	client, err := agentidentity.NewIdentityClient(getRegion())
	if err != nil {
		log.Fatalf("Failed to create identity client: %v", err)
	}

	doSTS := cmd == "sts" || cmd == "all"
	doAPIKey := cmd == "apikey" || cmd == "all"
	doOAuth := cmd == "oauth" || cmd == "all"

	if doSTS {
		fmt.Println("=== Get STS Credential ===")
		sts, err := agentidentity.GetSTSCredential(ctx, client)
		if err != nil {
			fmt.Printf("Get STS Credential failed: %v\n", err)
		} else {
			fmt.Printf("STS Credential AccessKeyId: %s, expires at: %s\n", sts.AccessKeyId, sts.Expiration)
		}
		fmt.Println()
	}

	if doAPIKey {
		fmt.Println("=== Get API Key ===")
		apiKey, err := agentidentity.GetAPIKey(ctx, client, provider)
		if err != nil {
			fmt.Printf("Get API Key failed: %v\n", err)
		} else {
			fmt.Printf("API Key: %s\n", maskString(apiKey, 4))
		}
		fmt.Println()
	}

	if doOAuth {
		fmt.Println("=== Get OAuth2 Token ===")
		token, err := getOAuth2TokenWithCallback(ctx, client, provider)
		if err != nil {
			fmt.Printf("Get OAuth2 Token failed: %v\n", err)
		} else {
			fmt.Printf("OAuth2 Token: %s\n", maskString(token, 4))
		}
	}
}

// getOAuth2TokenWithCallback starts a local HTTP server on a fixed port to
// receive the OAuth2 callback, confirms user auth, then polls for the token.
func getOAuth2TokenWithCallback(ctx context.Context, client *agentidentity.IdentityClient, providerName string) (string, error) {
	port := getCallbackPort()
	callbackURL := fmt.Sprintf("http://127.0.0.1:%d/callback", port)

	ctx, cancel := context.WithTimeout(ctx, 5*time.Minute)
	defer cancel()

	tokenC := make(chan string, 1)
	errC := make(chan error, 1)
	var once sync.Once

	userId, _ := agentidentity.GetUserId(ctx)
	userToken, _ := agentidentity.GetUserToken(ctx)

	mux := http.NewServeMux()
	mux.HandleFunc("/callback", func(w http.ResponseWriter, r *http.Request) {
		sessionURI := r.URL.Query().Get("session_uri")
		if sessionURI == "" {
			http.Error(w, "missing session_uri parameter", http.StatusBadRequest)
			return
		}
		once.Do(func() {
			fmt.Printf("Received callback, confirming user auth...\n")
			if err := client.ConfirmUserAuth(ctx, sessionURI,
				agentidentity.ConfirmUserAuthOption{
					UserId:    userId,
					UserToken: userToken,
				}); err != nil {
				fmt.Printf("ConfirmUserAuth error: %v\n", err)
			} else {
				fmt.Printf("User auth confirmed, waiting for token...\n")
			}
		})
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "Authorization received. You may close this tab.")
	})

	listener, err := net.Listen("tcp", fmt.Sprintf("127.0.0.1:%d", port))
	if err != nil {
		return "", fmt.Errorf("failed to listen on port %d: %w", port, err)
	}

	srv := &http.Server{Handler: mux, ReadHeaderTimeout: 10 * time.Second}
	go func() {
		if err := srv.Serve(listener); err != nil && err != http.ErrServerClosed {
			log.Printf("callback server error: %v", err)
		}
	}()
	defer srv.Close()

	fmt.Printf("Callback server listening on %s\n", callbackURL)

	go func() {
		token, err := agentidentity.GetOAuth2Token(ctx, client, providerName,
			agentidentity.GetTokenOptions{
				CallbackUrl: callbackURL,
				OnAuthUrl: func(authURL string) {
					fmt.Printf("\nPlease open this URL in your browser to authorize:\n\n  %s\n\n", authURL)
				},
			},
		)
		if err != nil {
			errC <- err
		} else {
			tokenC <- token
		}
	}()

	select {
	case token := <-tokenC:
		return token, nil
	case err := <-errC:
		return "", err
	case <-time.After(5 * time.Minute):
		return "", fmt.Errorf("timed out waiting for OAuth2 token")
	}
}

// getCallbackPort returns the callback port from AGENT_IDENTITY_CALLBACK_PORT
// env var, defaulting to 8443.
func getCallbackPort() int {
	portStr := os.Getenv("AGENT_IDENTITY_CALLBACK_PORT")
	if portStr == "" {
		return 8443
	}
	var port int
	if _, err := fmt.Sscanf(portStr, "%d", &port); err != nil || port <= 0 {
		return 8443
	}
	return port
}

// getRegion returns the region from environment or defaults to cn-beijing.
func getRegion() string {
	if region := os.Getenv("AGENT_IDENTITY_REGION_ID"); region != "" {
		return region
	}
	return "cn-beijing"
}

// maskString hides the middle of a string for safe display.
func maskString(s string, visibleLen int) string {
	if len(s) <= visibleLen*2 {
		return s
	}
	return s[:visibleLen] + "..." + s[len(s)-visibleLen:]
}
