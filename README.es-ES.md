

# 🔍✨ Habilidad de Agente para Raycast

![Banner de Raycast Agentic Skill](banner.png)

> Una Habilidad de Agente para Raycast: ayuda a tus asistentes de código IA con las mejores prácticas y flujos de trabajo para desarrollar, modificar y solucionar problemas en extensiones de Raycast (React/Node).

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Anthropic-purple)](https://claude.ai)
[![Gemini CLI](https://img.shields.io/badge/Gemini%20CLI-Google-blue)](https://github.com/google-gemini/gemini-cli)
[![Codex CLI](https://img.shields.io/badge/Codex%20CLI-OpenAI-green)](https://github.com/openai/codex)
[![Cursor](https://img.shields.io/badge/Cursor-AI%20IDE-orange)](https://cursor.sh)
[![Antigravity](https://img.shields.io/badge/Antigravity-DeepMind-red)](https://github.com/google-deepmind)
[![Agent Skills Standard](https://img.shields.io/badge/Agent%20Skills-Standard-blue.svg)](https://github.com/anthropics/skills)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## ✨ Descripción General de la Habilidad

Equipos a los agentes de IA con patrones y preferencias cruciales para desarrollar dentro del ecosistema de Raycast:

- 🏗️ **Plantillas y Configuración** — Mejores prácticas para duplicar o crear extensiones, gestionar `package.json` y el desarrollo local.
- 🎨 **Interfaz y Experiencia de Usuario** — Estándares para entradas de formulario, cierre automático al completar con `popToRoot`, y gestión de actualizaciones de iconos.
- 💾 **Obtención de Datos y Estado** — Uso de `@raycast/utils` y `useCachedPromise` para elementos de interfaz dinámicos.
- ⚙️ **Automatización y Ejecución Local** — Ejecución de scripts de AppleScript/Keyboard Maestro mediante `child_process.exec` y gestión nativa del Portapapeles.
- 🔐 **Preferencias y Autenticación** — Gestión de secretos requeridos y orientación adecuada para que los usuarios configuren tokens de API.

---

## 📋 Requisitos Previos

- **Raycast** instalado y en ejecución.
- **Node.js** y **npm** instalados.
- **API de Raycast** — inicializada para el desarrollo de extensiones (`npx @raycast/api@latest`).
- Un asistente de código IA que soporte el estándar de Agent Skills (ver plataformas a continuación).

---

## 🚀 Instalación e Integración

Esta colección de habilidades sigue el [estándard abierto de Agent Skills](https://github.com/anthropics/skills) y funciona en todas las principales plataformas de código IA.

### Tabla de Referencia Rápida

| **Plataforma**           | **Tipo** | **Ruta de Instalación**                | **Invocación**                      |
| ---------------------- | -------- | ------------------------------------ | ----------------------------------- |
| **Google Antigravity** | IDE      | `.agent/skills/raycast/`             | Invocación automática cuando sea relevante |
| **Claude Code**        | CLI      | `~/.claude/skills/raycast/`          | `Use the Raycast skill...`          |
| **Gemini CLI**         | CLI      | `~/.gemini/skills/raycast/`          | Invocación automática cuando sea relevante |
| **OpenCode**           | IDE      | `~/.config/opencode/skills/raycast/` | `skill({ name: "raycast" })`        |
| **Cursor IDE**         | IDE      | `.cursor/skills/raycast/`            | Mencionado en el chat con `@raycast`   |
| **OpenAI Codex**       | CLI      | `~/.codex/skills/raycast/`           | Invocación automática cuando sea relevante |

### Instalación

#### **Opción 1: Clonar desde GitHub** (Recomendada)

```bash
# Para Google Antigravity (habilidades de proyecto: colocar en la carpeta .agent de tu proyecto)
git clone https://github.com/adriangrantdotorg/Raycast-Skill.git .agent/skills

# Para Claude Code (habilidades globales)
git clone https://github.com/adriangrantdotorg/Raycast-Skill.git ~/.claude/skills/raycast

# Para Gemini CLI (habilidades globales)
git clone https://github.com/adriangrantdotorg/Raycast-Skill.git ~/.gemini/skills/raycast
```

#### **Opción 2: Instalación Manual**

1. Descarga la última versión.
2. Extrae y copia la(s) carpeta(s) de la habilidad deseada(s) al directorio de habilidades de tu plataforma.
3. Asegúrate de que cada habilidad tenga un archivo `SKILL.md` en su raíz.
4. Si es necesario, reinicia tu asistente IA o recarga el espacio de trabajo.

---

## 💡 Ejemplo de Uso

Una vez instalada, tu agente de IA aplicará automáticamente las mejores prácticas al trabajar con Raycast. Aquí tienes un ejemplo de prompt para probar:

### Automatización y Scripts Locales

```
"Crea un comando que ejecute mi macro específica de Keyboard Maestro."
```

El agente hará lo siguiente:

- Utilizará `child_process.exec` de Node para ejecutar `osascript`.
- Estructurará la ejecución del script de forma segura: `exec('osascript -e \'tell application "Keyboard Maestro Engine" to do script "MACRO_ID"\'')`.
- Manejará operaciones del portapapeles utilizando las utilidades nativas de Portapapeles de `@raycast/api`.

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Ya sea que estés agregando nuevas habilidades, refinando patrones existentes o mejorando la documentación, tu ayuda hace que este kit de herramientas sea mejor para toda la comunidad de Raycast 🙌🏾

**Inicio Rápido para Contribuyentes:**

```bash
# Bifurca y clona el repositorio
git clone https://github.com/adriangrantdotorg/Raycast-Skill.git
cd Raycast-Skill

# Crea una rama de características
git checkout -b feature/your-skill-or-fix

# Realiza tus cambios y pruébalos con tu agente de IA

# Confirma y envía
git commit -m "Add: description of your changes"
git push origin feature/your-skill-or-fix

# Abre un Pull Request en GitHub
```

---

## 📚 Recursos Adicionales

- **[Documentación de la API de Raycast](https://developers.raycast.com/)** — Referencia oficial de la API de extensiones
- **[Utilidades de Raycast](https://developers.raycast.com/utilities/)** — Utilidades auxiliares para hooks de React y más
- **[Especificación de Agent Skills](https://github.com/anthropics/skills)** — Documentación del estándar abierto
- **[Tienda de Raycast](https://www.raycast.com/store)** — Descubre lo que otros han construido
- **[Comunidad de Raycast](https://raycast.com/community)** — Soporte y discusión de la comunidad

---

## 🐛 Problemas y Soporte

¿Encontraste un problema o tienes una sugerencia?

- **Reportes de errores**: [Abre un issue](https://github.com/adriangrantdotorg/Raycast-Skill/issues/new?template=bug_report.md)
- **Solicitudes de características**: [Solicita una característica](https://github.com/adriangrantdotorg/Raycast-Skill/issues/new?template=feature_request.md)

---

<div align="center">
<sub>Construido con ❤️ para la comunidad de Raycast y flujos de trabajo impulsados por IA 🤖</sub>
</div>
