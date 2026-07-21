{ pkgs ? import <nixpkgs> {
    config = {
      allowUnfree = true;
    };
  }
}:
let
  my-vscode = pkgs.vscode-with-extensions.override {
    vscodeExtensions = with pkgs.vscode-extensions; [
      ms-azuretools.vscode-containers
      jnoortheen.nix-ide
      ms-python.python
    ];
  };
in
(pkgs.buildFHSEnv {
  name = "py-dev-env";
  targetPkgs = pkgs: [
    my-vscode
    pkgs.uv
    pkgs.python314
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
    pkgs.glib
  ];
  runScript = "bash";
}).env
