{ pkgs ? import <nixpkgs> {} }:

(pkgs.buildFHSEnv {
  name = "py-dev-env";
  targetPkgs = pkgs: [
    pkgs.uv
    pkgs.python313
    # Все системные библиотеки CUDA/CUDNN и т.д., если вы используете GPU
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
    pkgs.glib
  ];
  runScript = "bash";
}).env

