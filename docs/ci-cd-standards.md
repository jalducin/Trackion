# Estándares — CI/CD y disciplina spec-first

> Específicos de Trackion. Definen cómo se valida, publica y despliega el proyecto.

> **Estado actual (local-first):** el proyecto opera **local con Docker** (sin costos AWS). El despliegue
> a AWS está en modo **manual** (`workflow_dispatch`); el auto-deploy en push se reactiva recreando la
> infra (RDS/SSM) y el rol OIDC. El resto de esta guía describe el flujo cloud cuando esté activo.

## 1. Regla spec-first (obligatoria)

**Ningún código se escribe antes que su especificación.** Es el principio central de OpenSpec
(la documentación es la fuente de verdad). Para todo cambio:

1. `proposal` (¿por qué?) → `specs` (¿qué?, requisitos + escenarios verificables) → `design` (¿cómo?)
   → `tasks` (¿pasos?) → implementación → `verify` → `archive`.
2. Si aparece un arreglo/cambio entre `apply` y `archive`, **primero** se actualizan los artefactos del
   cambio (specs/escenarios/tasks) y luego el código (ver `docs/base-standards.md` §7).
3. Las ramas siguen `feature/[change-name]`; el primer paso de todo `tasks.md` es crear la rama.

## 2. Flujo de publicación y despliegue

| Momento | Quién | Acción |
|---|---|---|
| **1er push** | manual (sesión inicial) | `git push` del repo + crear repo público en GitHub |
| **1er deploy** | manual (sesión inicial) | `serverless deploy --stage develop` a AWS |
| **2da vez en adelante** | **CI/CD automático** | push a GitHub → GitHub Actions corre pruebas + `serverless package` → `serverless deploy` a AWS |

> A partir del segundo push, **no se despliega a mano**: el pipeline es la vía. Los deploys manuales
> quedan solo para emergencias documentadas.

## 3. Pipeline (GitHub Actions)

Archivo: `.github/workflows/deploy.yml`.

- **En Pull Request** (hacia `main`): instala deps, corre `pytest`, lint y `serverless package --stage develop`
  (valida que empaqueta, sin desplegar). Compuerta de calidad antes de mezclar.
- **En push a `main`**: repite validación y luego `serverless deploy --stage develop`.
- Credenciales AWS por **OIDC** (sin llaves de larga vida): el workflow asume el rol IAM
  `arn:aws:iam::957266312835:role/trackion-github-actions` (confianza acotada a `repo:jalducin/Trackion:ref:refs/heads/main`).
  Nunca credenciales en el código.
- Como el repo es **público**: jamás imprimir secretos en logs; los secrets de Actions no se exponen a
  PRs de forks por defecto; mantener `reference/` y `vendor/` fuera del repo (`.gitignore`).

## 4. Stages

- `develop` (default) → entorno de desarrollo/demostración.
- `staging` / `production` se activan creando los parámetros SSM `/staging|production/trackion/...`
  y desplegando con `--stage <stage>` (idealmente desde CI con protección de entorno).
