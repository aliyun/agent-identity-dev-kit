// Package config provides local JSON configuration file I/O.
package config

import (
	"encoding/json"
	"os"
	"sync"
)

const defaultConfigFile = ".config.json"

var fileMu sync.Mutex

// Write writes a key-value pair to the local configuration file.
// If filePath is empty, defaults to ".config.json".
func Write(key, value string, filePath ...string) error {
	configPath := defaultConfigFile
	if len(filePath) > 0 && filePath[0] != "" {
		configPath = filePath[0]
	}

	fileMu.Lock()
	defer fileMu.Unlock()

	configData := make(map[string]string)

	data, err := os.ReadFile(configPath)
	if err == nil {
		if jsonErr := json.Unmarshal(data, &configData); jsonErr != nil {
			configData = make(map[string]string)
		}
	}

	configData[key] = value

	output, err := json.MarshalIndent(configData, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(configPath, output, 0600)
}

// Read reads a value from the local configuration file.
// If filePath is empty, defaults to ".config.json".
func Read(key string, filePath ...string) (string, error) {
	configPath := defaultConfigFile
	if len(filePath) > 0 && filePath[0] != "" {
		configPath = filePath[0]
	}

	fileMu.Lock()
	defer fileMu.Unlock()

	data, err := os.ReadFile(configPath)
	if err != nil {
		return "", err
	}

	var configData map[string]string
	if err := json.Unmarshal(data, &configData); err != nil {
		return "", err
	}

	return configData[key], nil
}
