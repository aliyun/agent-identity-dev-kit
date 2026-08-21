package agentidentity

import (
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"

	credential "github.com/aliyun/credentials-go/credentials"
)

// mockServer wraps httptest.NewServer and provides a host:port endpoint
// without scheme. The darabonba-openapi SDK prepends "http://" or "https://"
// internally, so passing a full URL creates malformed URLs.
type mockServer struct {
	*httptest.Server
	endpoint string // host:port only, no scheme
}

func newMockServer(handler http.HandlerFunc) *mockServer {
	srv := httptest.NewServer(handler)
	u, _ := url.Parse(srv.URL)
	return &mockServer{Server: srv, endpoint: u.Host}
}

func newMockNetListener() net.Listener {
	l, _ := net.Listen("tcp", "127.0.0.1:0")
	return l
}

func setupMockCredentials() {
	os.Setenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "mock-ak-id")
	os.Setenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "mock-ak-secret")
}

func cleanupMockCredentials() {
	os.Unsetenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
	os.Unsetenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
}

// createMockCredential creates a credential.Credential using the mock env credentials.
func createMockCredential() credential.Credential {
	cred, err := credential.NewCredential(nil)
	if err != nil {
		panic(err)
	}
	return cred
}
