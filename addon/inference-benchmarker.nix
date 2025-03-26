{
  lib,
  rustPlatform,
  fetchFromGitHub,
  pkg-config,
  openssl,
}:

rustPlatform.buildRustPackage {
  pname = "inference-benchmarker";
  version = "unstable-2025-01-30";

  src = fetchFromGitHub {
    owner = "huggingface";
    repo = "inference-benchmarker";
    rev = "5d7d65e";
    hash = "sha256-vrbGr/1r8yLvuAaKttLByg7fmUu9nqfTrvHhZ4sPw2g=";
  };

  cargoLock = {
    lockFile = ./Cargo.lock;
  };

  postPatch = ''
    ln -s ${./Cargo.lock} Cargo.lock
  '';

  nativeBuildInputs = [
    pkg-config
  ];

  buildInputs = [
    openssl
  ];

  doCheck = false;

  meta = {
    description = "Inference server benchmarking tool";
    homepage = "https://github.com/huggingface/inference-benchmarker";
    license = lib.licenses.asl20;
    maintainers = with lib.maintainers; [ ];
    mainProgram = "inference-benchmarker";
  };
}
