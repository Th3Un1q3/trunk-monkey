group "default" {
  targets = ["local-cli"]
}

target "local-cli" {
  context = "."
  dockerfile = "Dockerfile"
  tags = ["trunk-monkey:beta"]
}