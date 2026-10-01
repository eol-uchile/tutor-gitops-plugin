# Tutor GitOps Plugin

Plugin de Tutor diseñado para generar manifiestos de Kubernetes compatibles con GitOps (ArgoCD, Kustomize).

Este plugin transforma la salida estándar de Tutor para adaptarla a la infraestructura de Kubernetes, incluyendo integraciones como SealedSecrets, modificaciones a los Deployments, etc.

## Instalación

Este plugin se debe instalar en el entorno virtual de la instancia de Tutor.

Para instalarlo directamente desde Git apuntando a la rama de release de tu versión de Tutor (ej. Lilac):

```bash
# Apuntando a la rama release (recibe actualizaciones de la versión):
pip install git+https://github.com/eol-uchile/tutor-gitops-plugin.git@eol-release/lilac.master

# O apuntando a un tag específico (versión inmutable):
pip install git+https://github.com/eol-uchile/tutor-gitops-plugin.git@eol-release/lilac.1
```

## Uso

Una vez instalado, habilite el plugin con:

```bash
tutor plugins enable gitops
```

Luego, cuando se ejecute el guardado de configuración, el plugin aplicará sus parches:

```bash
tutor config save
```

## Desarrollo Local

Para trabajar localmente en este plugin:

1. Clona el repositorio:
```bash
git clone https://github.com/eol-uchile/tutor-gitops-plugin.git
cd tutor-gitops-plugin
```

2. Instálalo en modo editable en el entorno virtual de Tutor:
```bash
pip install -e .
```

Cualquier cambio que se realice en el código se reflejará la próxima vez que se ejecute un comando `tutor config save`.

## Estrategia de Ramas y Releases

El plugin sigue el modelo de ramificación de Open edX para soportar múltiples versiones mayores de Tutor de forma desacoplada (permitiendo backports y fixes independientes por constelación):

* **`main`**: Rama para el desarrollo continuo del plugin.
* **`eol-release/<nombre-arbol>.master`**: Rama de release por versión de Open edX (ej. `eol-release/lilac.master`, `eol-release/sumac.master`).
* **Tags `eol-release/<nombre-arbol>.<patch>`**: Versiones estables publicadas (ej. `eol-release/lilac.1`, `eol-release/lilac.2`).

### Flujo de trabajo para Releases y Backports

#### 1. Crear una nueva rama de release para una versión de Tutor:
```bash
git checkout main
git checkout -b eol-release/<nombre-arbol>.master
git push -u origin eol-release/<nombre-arbol>.master
```

#### 2. Publicar una nueva versión (tag):
```bash
git checkout eol-release/<nombre-arbol>.master
git tag eol-release/<nombre-arbol>.<numero-patch>
git push origin eol-release/<nombre-arbol>.<numero-patch>
```
*Ejemplo:* `git tag eol-release/lilac.1 && git push origin eol-release/lilac.1`

#### 3. Aplicar un fix o backport a una versión antigua:
1. Hacer checkout a la rama de la versión requerida: `git checkout eol-release/lilac.master`
2. Aplicar el cambio o hacer cherry-pick del commit: `git cherry-pick <commit-hash>`
3. Empujar el commit a la rama: `git push origin eol-release/lilac.master`
4. Generar el siguiente tag de parche:
   ```bash
   git tag eol-release/lilac.2
   git push origin eol-release/lilac.2
   ```

## Estructura

* `setup.py` y `pyproject.toml`: Configuración del paquete y dependencias.
* `gitops/`: Código fuente principal.
* `gitops/transformers/`: Módulos encargados de transformar las plantillas nativas de Tutor a manifiestos GitOps.
