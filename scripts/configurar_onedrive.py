"""Convierte la configuración local a rutas portables; nunca escribe en los Excel."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import ConfigError, portable_settings, read_settings, resolve_sources
from reader import FormatError, read_xlsx


def verify(settings, config_dir):
    resolved = resolve_sources(settings, config_dir)
    for name, kind in (("imports", "import"), ("exports", "export")):
        source = resolved[name]
        read_xlsx(source["path"], kind, source.get("sheet"), source.get("headerRow"),
                  resolved.get("dateOrder", "MDY"))


def write_config(config, settings):
    # Guardar el primer respaldo sin reemplazarlo; no publicar ninguno de los dos archivos.
    backup = config.with_name(config.name + ".bak")
    try:
        descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(config.read_bytes())
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=config.parent,
                                         prefix=config.name + ".", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(settings, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, config)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Detectar OneDrive y comprobar ambos itinerarios localmente.")
    parser.add_argument("--config", required=True, help="Archivo de configuración externo al proyecto.")
    parser.add_argument("--check", action="store_true", help="Comprobar sin modificar la configuración.")
    args = parser.parse_args()
    try:
        config = Path(args.config).resolve()
        settings = read_settings(config)
        if args.check:
            verify(settings, config.parent)
            print("Comprobación correcta: ambos Excel se pueden leer con los encabezados configurados.")
            print("No se modificó la configuración ni los Excel. La frescura de OneDrive se verifica por separado.")
            return 0
        portable = portable_settings(settings, config.parent)
        verify(portable, config.parent)
        if portable != settings:
            write_config(config, portable)
            print("Configuración adaptada a OneDrive. Respaldo .bak junto a la configuración original.")
        else:
            print("La configuración ya utiliza rutas portables de OneDrive.")
        print("Ambos Excel se leyeron correctamente. No se modificaron los itinerarios.")
        return 0
    except (ConfigError, FormatError) as exc:
        print(str(exc), file=sys.stderr)
    except (OSError, ValueError):
        print("No se pudo completar la comprobación. Revisar permisos, disponibilidad local y configuración.", file=sys.stderr)
    except Exception:
        print("No se pudieron leer ambos itinerarios. Revisar archivos y sincronización con IT.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
