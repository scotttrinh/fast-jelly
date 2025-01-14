{
  description = "Dev environment";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils }: flake-utils.lib.eachDefaultSystem (system:
  let
    pkgs = import nixpkgs { inherit system; };
  in {
    devShells.default = pkgs.mkShell {
      packages = [ pkgs.python312 pkgs.poetry pkgs.ruff pkgs.mailpit ];

      shellHook = ''
        export APP_PORT=8000
        export MP_SMTP_AUTH=smtpuser:smtppassword
      '';
    };
  });
}
