{
  lib,
  buildNpmPackage,
  fetchFromGitHub,
}:

buildNpmPackage rec {
  pname = "mcp-inspector";
  version = "0.7.0";

  src = fetchFromGitHub {
    owner = "modelcontextprotocol";
    repo = "inspector";
    rev = version;
    hash = "sha256-+5MlVuEXN1h9rLQj0JlXJArUsCCD1OIyJMELPwRLVZs=";
  };

  meta = {
    description = "Visual testing tool for MCP servers";
    homepage = "https://github.com/modelcontextprotocol/inspector";
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ taha-yassine ];
    mainProgram = "mcp-inspector";
    platforms = lib.platforms.all;
  };
}
