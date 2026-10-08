"""Configuración externa y rutas locales. No inicia sesión ni sincroniza OneDrive."""
from copy import deepcopy
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath


SOURCES = ("imports", "exports")


class ConfigError(Exception):
    """Mensajes de diagnóstico sin rutas privadas ni contenido del JSON."""


def read_settings(config):
    try:
        settings = json.loads(Path(config).read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Configuración JSON inválida: línea {exc.lineno}, columna {exc.colno}. "
                          "Revisar comillas, comas y usar / en las rutas.") from None
    except (OSError, UnicodeError):
        raise ConfigError("No se pudo abrir la configuración local en UTF-8.") from None
    if not isinstance(settings, dict):
        raise ConfigError("La configuración debe ser un objeto JSON.")
    for name in SOURCES:
        source = settings.get(name)
        if not isinstance(source, dict) or not isinstance(source.get("path"), str) or not source["path"].strip():
            raise ConfigError(f"Falta una ruta válida en {name}.")
        if source.get("pathBase", "config") not in ("config", "onedrive"):
            raise ConfigError(f"pathBase en {name} debe ser config u onedrive.")
    return settings


def _registry_business_roots():
    if os.name != "nt":
        return []
    import winreg
    roots = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\OneDrive\Accounts") as accounts:
            index = 0
            while True:
                try:
                    name = winreg.EnumKey(accounts, index)
                except OSError:
                    break
                index += 1
                if not name.casefold().startswith("business"):
                    continue
                try:
                    with winreg.OpenKey(accounts, name) as account:
                        value, kind = winreg.QueryValueEx(account, "UserFolder")
                        if kind in (winreg.REG_SZ, winreg.REG_EXPAND_SZ) and isinstance(value, str):
                            roots.append(os.path.expandvars(value) if kind == winreg.REG_EXPAND_SZ else value)
                except OSError:
                    continue
    except OSError:
        pass
    return roots


def business_onedrive_roots(environ=None):
    """Solo cuentas empresariales del usuario que ejecuta el proceso; no busca en el disco."""
    environ = os.environ if environ is None else environ
    values = [environ.get("OneDriveCommercial", ""), *_registry_business_roots()]
    roots, seen = [], set()
    for value in values:
        if not value:
            continue
        try:
            path = Path(value).resolve()
            key = os.path.normcase(str(path))
            if path.is_dir() and key not in seen:
                seen.add(key)
                roots.append(path)
        except (OSError, ValueError):
            continue
    return roots


def _candidate_roots(environ=None, roots=None):
    environ = os.environ if environ is None else environ
    override = environ.get("TECHTOP_ONEDRIVE_ROOT", "").strip()
    if override:
        try:
            root = Path(override).resolve()
            if root.is_dir():
                return [root]
        except (OSError, ValueError):
            pass
        raise ConfigError("TECHTOP_ONEDRIVE_ROOT no apunta a una carpeta local disponible.")
    return business_onedrive_roots(environ) if roots is None else list(roots)


def _relative_path(value):
    normalized = value.replace("\\", "/")
    posix, windows = PurePosixPath(normalized), PureWindowsPath(normalized)
    if posix.is_absolute() or windows.drive or windows.root or ".." in posix.parts or not posix.parts:
        raise ConfigError("Una ruta OneDrive debe ser interna, sin unidad de disco ni segmentos ..")
    return Path(*posix.parts)


def _within_root(root, relative):
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ConfigError("La ruta OneDrive sale de la carpeta autorizada.")
    return target


def _select_match(matches):
    if not matches:
        raise ConfigError("No se encontró un OneDrive empresarial con los archivos configurados. "
                          "Revisar sincronización, rutas internas y cuenta de ejecución; "
                          "IT puede indicar TECHTOP_ONEDRIVE_ROOT.")
    if len(matches) > 1:
        raise ConfigError("Hay más de un OneDrive válido. IT debe indicar TECHTOP_ONEDRIVE_ROOT "
                          "para elegir la cuenta correcta.")
    return matches[0]


def resolve_sources(settings, config_dir, environ=None, roots=None):
    resolved = deepcopy(settings)
    relative = {name: _relative_path(settings[name]["path"]) for name in SOURCES
                if settings[name].get("pathBase", "config") == "onedrive"}
    if relative:
        matches = []
        for candidate in _candidate_roots(environ, roots):
            root = Path(candidate).resolve()
            try:
                targets = {name: _within_root(root, value) for name, value in relative.items()}
                if all(path.is_file() for path in targets.values()):
                    matches.append(targets)
            except (OSError, ConfigError):
                continue
        targets = _select_match(matches)
        for name, path in targets.items():
            resolved[name]["path"] = str(path)
    for name in SOURCES:
        if name not in relative:
            path = Path(settings[name]["path"])
            resolved[name]["path"] = str(path if path.is_absolute() else Path(config_dir) / path)
    return resolved


def load_settings(config, environ=None, roots=None):
    return resolve_sources(read_settings(config), Path(config).resolve().parent, environ, roots)


def portable_settings(settings, config_dir, environ=None, roots=None):
    """Convierte las dos rutas existentes sin modificar archivos ni adivinar nombres."""
    sources = {}
    for name in SOURCES:
        source = settings[name]
        if source.get("pathBase", "config") == "onedrive":
            sources[name] = (True, _relative_path(source["path"]))
        else:
            path = Path(source["path"])
            sources[name] = (False, (path if path.is_absolute() else Path(config_dir) / path).resolve())
    matches = []
    for candidate in _candidate_roots(environ, roots):
        root = Path(candidate).resolve()
        converted = deepcopy(settings)
        try:
            for name, (is_relative, path) in sources.items():
                target = _within_root(root, path) if is_relative else path
                internal = target.relative_to(root)
                if not target.is_file():
                    break
                converted[name]["path"] = internal.as_posix()
                converted[name]["pathBase"] = "onedrive"
            else:
                matches.append(converted)
        except (ValueError, OSError, ConfigError):
            continue
    return _select_match(matches)
