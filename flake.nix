{
  description = "Python devshell";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    nixpkgs-stable.url = "nixpkgs/nixos-24.11";

    sidem = {
      url = "github:taha-yassine/sidem";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    nixpkgs-stable,
    sidem,
  }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      config = {
        allowUnfree = true;
        cudaSupport = true;
      };
    };
    pkgs-stable = import nixpkgs-stable {
      inherit system;
    };

    python =
      if builtins.pathExists ./.python-version
      then
        let
          pythonVersion = builtins.readFile ./.python-version;
        in
          pkgs."python${builtins.substring 0 3 (builtins.replaceStrings [ "." "\n" ] [ "" "" ] pythonVersion)}"
      else pkgs.python3;

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
        (python.withPackages (ps: with ps; [
          uv-build
        ]))
        uv
        just
        devcontainer

        # (callPackage ./llama-cpp.nix {
        #   rocmSupport = true;
        # })
        # (llama-cpp.overrideAttrs (oldAttrs: {
        #   src = /home/tyassine/code/llama.cpp;
        # }))
        # llama-cpp
        
        # (callPackage ./inference-benchmarker.nix {})
        # (callPackage ./mcp-inspector.nix {})

        sidem.packages.${system}.default
      ] ++ (with pkgs-stable; [
        mitmproxy
      ]);
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
