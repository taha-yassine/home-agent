{
  description = "Python devshell";

  # nixConfig = {
  #   extra-trusted-substituters = [
  #     "https://nix-community.cachix.org"
  #   ];
  #   extra-trusted-public-keys = [
  #     "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
  #   ];
  # };

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      config = {
        allowUnfree = true;
        cudaSupport = true;
      };
    };

    libs = [
      # pkgs.cudaPackages.cudatoolkit
      # pkgs.cudaPackages.cudnn
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib

      # Where your local "lib/libcuda.so" lives. If you're not on NixOS, you
      # should provide the right path (likely another one).
      "/run/opengl-driver"
    ];

    shell = pkgs.mkShell {
      packages = with pkgs; [
        python312
        uv
        just

        # (callPackage ./llama-cpp.nix {
        #   rocmSupport = true;
        # })
        llama-cpp
        mitmproxy

        # (callPackage ./inference-benchmarker.nix {})
        (callPackage ./mcp-inspector.nix {})
      ];
      env = {
        CC = "${pkgs.gcc}/bin/gcc";
        LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath libs;

        UVICORN_LOG_LEVEL = "debug";
        DEBUGPY = "true";
      };
    };
  in {
    devShells.${system}.default = shell;
  };
}