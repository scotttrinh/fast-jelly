{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/basics/
  # env.GREET = "devenv";

  # https://devenv.sh/packages/
  packages = [ pkgs.httpie pkgs.ruff ];

  # https://devenv.sh/languages/
  # languages.rust.enable = true;
  languages.python = {
    enable = true;
    version = "3.12";
    poetry = {
      enable = true;
      activate.enable = true;
      install.enable = true;
    };
  };

  # https://devenv.sh/processes/
  # processes.cargo-watch.exec = "cargo-watch";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  # scripts.hello.exec = ''
  #   echo hello from $GREET
  # '';
  scripts.dev.exec = "uvicorn app.main:fast_api --port 5001 --reload";
  scripts.dtr.exec = ''
    devenv tasks run "$@"
  '';

  enterShell = ''
    python --version
  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };
  tasks = {
    "db:migration:create".exec = "edgedb migration create";
    "db:migration:create".after = ["db:migration:apply"];
    "db:migration:apply".exec = "edgedb migration apply";
    "db:generate".exec = "edgedb-py";
    "db:migration:apply".after = ["db:generate"];
  };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
  '';

  # https://devenv.sh/pre-commit-hooks/
  # pre-commit.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
