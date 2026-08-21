package agentidentity

import (
	"github.com/aliyun/agent-identity-dev-kit/agent-identity-sdk-go/internal/config"
)

// WriteLocalConfig writes a key-value pair to the local configuration file.
// If filePath is empty, defaults to ".config.json".
func WriteLocalConfig(key, value string, filePath ...string) error {
	return config.Write(key, value, filePath...)
}

// ReadLocalConfig reads a value from the local configuration file.
// If filePath is empty, defaults to ".config.json".
// Returns empty string and error if file doesn't exist or JSON is invalid.
func ReadLocalConfig(key string, filePath ...string) (string, error) {
	return config.Read(key, filePath...)
}
