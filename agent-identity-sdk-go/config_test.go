package agentidentity

import (
	"os"
	"path/filepath"
	"testing"
)

// ============================================================================
// config.go tests
// ============================================================================

func TestWriteLocalConfig(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test-config.json")

	err := WriteLocalConfig("key1", "value1", path)
	if err != nil {
		t.Fatalf("WriteLocalConfig failed: %v", err)
	}

	val, err := ReadLocalConfig("key1", path)
	if err != nil {
		t.Fatalf("ReadLocalConfig failed: %v", err)
	}
	if val != "value1" {
		t.Fatalf("expected value1, got %s", val)
	}
}

func TestWriteLocalConfig_Append(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test-config.json")

	WriteLocalConfig("key1", "value1", path)
	WriteLocalConfig("key2", "value2", path)

	val, err := ReadLocalConfig("key1", path)
	if err != nil {
		t.Fatalf("ReadLocalConfig failed: %v", err)
	}
	if val != "value1" {
		t.Fatalf("expected key1=value1, got %s", val)
	}

	val2, err := ReadLocalConfig("key2", path)
	if err != nil {
		t.Fatalf("ReadLocalConfig failed: %v", err)
	}
	if val2 != "value2" {
		t.Fatalf("expected key2=value2, got %s", val2)
	}
}

func TestWriteLocalConfig_UpdateExisting(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test-config.json")

	WriteLocalConfig("key1", "value1", path)
	WriteLocalConfig("key1", "value2", path)

	val, _ := ReadLocalConfig("key1", path)
	if val != "value2" {
		t.Fatalf("expected key1=value2, got %s", val)
	}
}

func TestWriteLocalConfig_InvalidJsonReset(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test-config.json")

	os.WriteFile(path, []byte("not-json"), 0644)

	err := WriteLocalConfig("key1", "value1", path)
	if err != nil {
		t.Fatalf("WriteLocalConfig failed with invalid json file: %v", err)
	}

	val, _ := ReadLocalConfig("key1", path)
	if val != "value1" {
		t.Fatalf("expected key1=value1, got %s", val)
	}
}

func TestReadLocalConfig_FileNotFound(t *testing.T) {
	_, err := ReadLocalConfig("key", "/nonexistent/path")
	if err == nil {
		t.Fatal("expected error for non-existent file")
	}
}

func TestReadLocalConfig_InvalidJson(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "bad.json")
	os.WriteFile(path, []byte("not-json"), 0644)

	_, err := ReadLocalConfig("key", path)
	if err == nil {
		t.Fatal("expected error for invalid JSON")
	}
}

func TestReadLocalConfig_KeyNotFound(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test-config.json")
	WriteLocalConfig("existing", "value", path)

	val, err := ReadLocalConfig("nonexistent", path)
	if err != nil {
		t.Fatalf("ReadLocalConfig failed: %v", err)
	}
	if val != "" {
		t.Fatalf("expected empty string, got %s", val)
	}
}

func TestDefaultConfigFile(t *testing.T) {
	dir := t.TempDir()
	testPath := filepath.Join(dir, ".config.json")

	err := WriteLocalConfig("testkey", "testval", testPath)
	if err != nil {
		t.Fatalf("WriteLocalConfig failed: %v", err)
	}

	val, err := ReadLocalConfig("testkey", testPath)
	if err != nil {
		t.Fatalf("ReadLocalConfig failed: %v", err)
	}
	if val != "testval" {
		t.Fatalf("expected testval, got %s", val)
	}
}

func TestWriteLocalConfig_DefaultPath(t *testing.T) {
	dir := t.TempDir()
	oldCwd, _ := os.Getwd()
	os.Chdir(dir)
	defer os.Chdir(oldCwd)

	err := WriteLocalConfig("cwd-key", "cwd-val")
	if err != nil {
		t.Fatalf("WriteLocalConfig failed: %v", err)
	}
	val, err := ReadLocalConfig("cwd-key")
	if err != nil {
		t.Fatalf("ReadLocalConfig failed: %v", err)
	}
	if val != "cwd-val" {
		t.Fatalf("expected cwd-val, got %s", val)
	}
	os.Remove(".config.json")
}
