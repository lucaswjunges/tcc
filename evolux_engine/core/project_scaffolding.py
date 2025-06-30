import os
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime
import shutil
import jinja2

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.config.advanced_config import AdvancedSystemConfig

logger = get_structured_logger("project_scaffolding")

class ProjectType(Enum):
    """Tipos de projeto suportados"""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    MICROSERVICE = "microservice"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    DATA_SCIENCE = "data_science"
    ML_MODEL = "ml_model"
    BLOCKCHAIN = "blockchain"
    GAME = "game"
    DOCUMENTATION = "documentation"

class Framework(Enum):
    """Frameworks suportados"""
    # Web Frameworks
    FLASK = "flask"
    DJANGO = "django"
    FASTAPI = "fastapi"
    EXPRESS = "express"
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    NEXTJS = "nextjs"
    
    # Mobile
    REACT_NATIVE = "react_native"
    FLUTTER = "flutter"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    
    # Desktop
    ELECTRON = "electron"
    TKINTER = "tkinter"
    QT = "qt"
    
    # Data Science
    JUPYTER = "jupyter"
    STREAMLIT = "streamlit"
    DASH = "dash"
    
    # Others
    VANILLA = "vanilla"

@dataclass
class FileTemplate:
    """Template para geração de arquivo"""
    name: str
    path: str
    content: str
    is_template: bool = True
    executable: bool = False
    variables: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DirectoryStructure:
    """Estrutura de diretórios"""
    name: str
    path: str
    files: List[FileTemplate] = field(default_factory=list)
    subdirectories: List['DirectoryStructure'] = field(default_factory=list)

@dataclass
class ProjectScaffold:
    """Scaffold completo de projeto"""
    name: str
    description: str
    project_type: ProjectType
    framework: Framework
    language: str
    root_directory: DirectoryStructure
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    scripts: Dict[str, str] = field(default_factory=dict)
    env_vars: Dict[str, str] = field(default_factory=dict)
    documentation: List[str] = field(default_factory=list)

class IntelligentProjectScaffolding:
    """
    Sistema inteligente de scaffolding que:
    - Analisa o goal do projeto para determinar tipo e tecnologias
    - Gera estrutura de projeto otimizada
    - Cria templates personalizados
    - Configura dependências e scripts
    - Implementa melhores práticas
    """
    
    def __init__(self, config: AdvancedSystemConfig):
        self.config = config
        self.templates_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            autoescape=jinja2.select_autoescape()
        )
        
        # Mapeamentos inteligentes
        self.project_type_keywords = self._build_project_type_keywords()
        self.framework_recommendations = self._build_framework_recommendations()
        self.default_scaffolds = self._build_default_scaffolds()
        
        logger.info("IntelligentProjectScaffolding initialized")
    
    def _build_project_type_keywords(self) -> Dict[ProjectType, List[str]]:
        """Constrói mapeamento de palavras-chave para tipos de projeto"""
        return {
            ProjectType.WEB_APPLICATION: [
                "website", "web app", "web application", "portal", "dashboard",
                "frontend", "ui", "interface", "site", "blog", "cms"
            ],
            ProjectType.API_SERVICE: [
                "api", "rest", "graphql", "service", "backend", "microservice",
                "endpoint", "server", "rest api", "web service", "express api"
            ],
            ProjectType.CLI_TOOL: [
                "cli", "command line", "terminal", "console", "script",
                "tool", "utility", "automation", "command"
            ],
            ProjectType.LIBRARY: [
                "library", "package", "module", "framework", "sdk",
                "component", "utility library", "toolkit"
            ],
            ProjectType.MICROSERVICE: [
                "microservice", "micro service", "distributed", "scalable service",
                "container", "kubernetes", "docker service"
            ],
            ProjectType.MOBILE_APP: [
                "mobile", "app", "android", "ios", "mobile app",
                "smartphone", "tablet", "cross-platform"
            ],
            ProjectType.DESKTOP_APP: [
                "desktop", "desktop app", "gui", "application",
                "windows app", "mac app", "linux app"
            ],
            ProjectType.DATA_SCIENCE: [
                "data science", "analytics", "data analysis", "jupyter",
                "notebook", "visualization", "data viz", "etl"
            ],
            ProjectType.ML_MODEL: [
                "machine learning", "ml", "ai", "model", "neural network",
                "deep learning", "training", "prediction", "classification"
            ],
            ProjectType.BLOCKCHAIN: [
                "blockchain", "crypto", "smart contract", "web3",
                "ethereum", "defi", "nft", "cryptocurrency"
            ],
            ProjectType.GAME: [
                "game", "gaming", "unity", "pygame", "game engine",
                "2d game", "3d game", "arcade", "simulation"
            ],
            ProjectType.DOCUMENTATION: [
                "documentation", "docs", "guide", "manual", "tutorial",
                "readme", "wiki", "knowledge base"
            ]
        }
    
    def _build_framework_recommendations(self) -> Dict[ProjectType, List[Framework]]:
        """Recomendações de framework por tipo de projeto"""
        return {
            ProjectType.WEB_APPLICATION: [Framework.REACT, Framework.VUE, Framework.NEXTJS, Framework.FLASK],
            ProjectType.API_SERVICE: [Framework.FASTAPI, Framework.FLASK, Framework.EXPRESS, Framework.DJANGO],
            ProjectType.CLI_TOOL: [Framework.VANILLA],
            ProjectType.LIBRARY: [Framework.VANILLA],
            ProjectType.MICROSERVICE: [Framework.FASTAPI, Framework.EXPRESS, Framework.FLASK],
            ProjectType.MOBILE_APP: [Framework.REACT_NATIVE, Framework.FLUTTER],
            ProjectType.DESKTOP_APP: [Framework.ELECTRON, Framework.TKINTER, Framework.QT],
            ProjectType.DATA_SCIENCE: [Framework.JUPYTER, Framework.STREAMLIT, Framework.DASH],
            ProjectType.ML_MODEL: [Framework.JUPYTER, Framework.STREAMLIT],
            ProjectType.BLOCKCHAIN: [Framework.VANILLA],
            ProjectType.GAME: [Framework.VANILLA],
            ProjectType.DOCUMENTATION: [Framework.VANILLA]
        }
    
    def _build_default_scaffolds(self) -> Dict[str, ProjectScaffold]:
        """Scaffolds padrão para diferentes combinações projeto/framework"""
        scaffolds = {}
        
        # Flask Web Application
        scaffolds["web_app_flask"] = ProjectScaffold(
            name="Flask Web Application",
            description="Full-featured Flask web application with best practices",
            project_type=ProjectType.WEB_APPLICATION,
            framework=Framework.FLASK,
            language="python",
            root_directory=self._create_flask_structure(),
            dependencies={
                "python": ["flask", "flask-sqlalchemy", "flask-migrate", "python-dotenv", "requests"]
            },
            scripts={
                "start": "python app.py",
                "test": "python -m pytest tests/",
                "lint": "flake8 .",
                "format": "black ."
            },
            env_vars={
                "FLASK_ENV": "development",
                "SECRET_KEY": "your-secret-key-here",
                "DATABASE_URL": "sqlite:///app.db"
            }
        )
        
        # FastAPI Service
        scaffolds["api_fastapi"] = ProjectScaffold(
            name="FastAPI REST Service",
            description="High-performance FastAPI REST service with documentation",
            project_type=ProjectType.API_SERVICE,
            framework=Framework.FASTAPI,
            language="python",
            root_directory=self._create_fastapi_structure(),
            dependencies={
                "python": ["fastapi", "uvicorn", "pydantic", "sqlalchemy", "alembic", "python-jose", "passlib"]
            },
            scripts={
                "start": "uvicorn main:app --reload",
                "test": "pytest tests/",
                "docs": "python -c \"import webbrowser; webbrowser.open('http://localhost:8000/docs')\""
            }
        )
        
        # React Application
        scaffolds["web_app_react"] = ProjectScaffold(
            name="React Web Application",
            description="Modern React application with TypeScript and best practices",
            project_type=ProjectType.WEB_APPLICATION,
            framework=Framework.REACT,
            language="typescript",
            root_directory=self._create_react_structure(),
            dependencies={
                "npm": ["react", "react-dom", "@types/react", "@types/react-dom", "typescript", "vite"]
            },
            scripts={
                "start": "npm run dev",
                "build": "npm run build",
                "test": "npm test",
                "lint": "eslint src/"
            }
        )
        
        return scaffolds
    
    def _create_flask_structure(self) -> DirectoryStructure:
        """Cria estrutura para aplicação Flask"""
        return DirectoryStructure(
            name="flask_app",
            path=".",
            files=[
                FileTemplate("app.py", "app.py", self._get_flask_app_template()),
                FileTemplate("config.py", "config.py", self._get_flask_config_template()),
                FileTemplate("requirements.txt", "requirements.txt", "flask\nflask-sqlalchemy\nflask-migrate\npython-dotenv\nrequests\n"),
                FileTemplate(".env", ".env", "FLASK_ENV=development\nSECRET_KEY=your-secret-key-here\nDATABASE_URL=sqlite:///app.db\n"),
                FileTemplate("README.md", "README.md", self._get_readme_template("Flask Web Application")),
                FileTemplate(".gitignore", ".gitignore", self._get_python_gitignore())
            ],
            subdirectories=[
                DirectoryStructure(
                    name="app",
                    path="app",
                    files=[
                        FileTemplate("__init__.py", "app/__init__.py", ""),
                        FileTemplate("models.py", "app/models.py", self._get_flask_models_template()),
                        FileTemplate("routes.py", "app/routes.py", self._get_flask_routes_template())
                    ]
                ),
                DirectoryStructure(
                    name="tests",
                    path="tests",
                    files=[
                        FileTemplate("__init__.py", "tests/__init__.py", ""),
                        FileTemplate("test_app.py", "tests/test_app.py", self._get_flask_test_template())
                    ]
                ),
                DirectoryStructure(
                    name="static",
                    path="static",
                    subdirectories=[
                        DirectoryStructure(name="css", path="static/css"),
                        DirectoryStructure(name="js", path="static/js"),
                        DirectoryStructure(name="images", path="static/images")
                    ]
                ),
                DirectoryStructure(
                    name="templates",
                    path="templates",
                    files=[
                        FileTemplate("base.html", "templates/base.html", self._get_flask_base_template()),
                        FileTemplate("index.html", "templates/index.html", self._get_flask_index_template())
                    ]
                )
            ]
        )
    
    def _create_fastapi_structure(self) -> DirectoryStructure:
        """Cria estrutura para serviço FastAPI"""
        return DirectoryStructure(
            name="fastapi_service",
            path=".",
            files=[
                FileTemplate("main.py", "main.py", self._get_fastapi_main_template()),
                FileTemplate("requirements.txt", "requirements.txt", "fastapi\nuvicorn\npydantic\nsqlalchemy\nalembic\n"),
                FileTemplate("README.md", "README.md", self._get_readme_template("FastAPI REST Service")),
                FileTemplate(".gitignore", ".gitignore", self._get_python_gitignore())
            ],
            subdirectories=[
                DirectoryStructure(
                    name="app",
                    path="app",
                    files=[
                        FileTemplate("__init__.py", "app/__init__.py", ""),
                        FileTemplate("models.py", "app/models.py", self._get_fastapi_models_template()),
                        FileTemplate("schemas.py", "app/schemas.py", self._get_fastapi_schemas_template()),
                        FileTemplate("crud.py", "app/crud.py", self._get_fastapi_crud_template()),
                        FileTemplate("database.py", "app/database.py", self._get_fastapi_database_template())
                    ],
                    subdirectories=[
                        DirectoryStructure(
                            name="routers",
                            path="app/routers",
                            files=[
                                FileTemplate("__init__.py", "app/routers/__init__.py", ""),
                                FileTemplate("items.py", "app/routers/items.py", self._get_fastapi_router_template())
                            ]
                        )
                    ]
                ),
                DirectoryStructure(
                    name="tests",
                    path="tests",
                    files=[
                        FileTemplate("__init__.py", "tests/__init__.py", ""),
                        FileTemplate("test_main.py", "tests/test_main.py", self._get_fastapi_test_template())
                    ]
                )
            ]
        )
    
    def _create_react_structure(self) -> DirectoryStructure:
        """Cria estrutura para aplicação React"""
        return DirectoryStructure(
            name="react_app",
            path=".",
            files=[
                FileTemplate("package.json", "package.json", self._get_react_package_template()),
                FileTemplate("tsconfig.json", "tsconfig.json", self._get_react_tsconfig_template()),
                FileTemplate("vite.config.ts", "vite.config.ts", self._get_react_vite_config_template()),
                FileTemplate("index.html", "index.html", self._get_react_index_template()),
                FileTemplate("README.md", "README.md", self._get_readme_template("React Web Application")),
                FileTemplate(".gitignore", ".gitignore", self._get_node_gitignore())
            ],
            subdirectories=[
                DirectoryStructure(
                    name="src",
                    path="src",
                    files=[
                        FileTemplate("main.tsx", "src/main.tsx", self._get_react_main_template()),
                        FileTemplate("App.tsx", "src/App.tsx", self._get_react_app_template()),
                        FileTemplate("App.css", "src/App.css", self._get_react_css_template())
                    ],
                    subdirectories=[
                        DirectoryStructure(name="components", path="src/components"),
                        DirectoryStructure(name="hooks", path="src/hooks"),
                        DirectoryStructure(name="utils", path="src/utils"),
                        DirectoryStructure(name="assets", path="src/assets")
                    ]
                ),
                DirectoryStructure(name="public", path="public")
            ]
        )
    
    def analyze_project_goal(self, goal: str) -> Dict[str, Any]:
        """Analisa o goal do projeto para determinar tipo e tecnologias"""
        goal_lower = goal.lower()
        
        # Determinar tipo de projeto
        project_type_scores = {}
        for proj_type, keywords in self.project_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in goal_lower)
            if score > 0:
                project_type_scores[proj_type] = score
        
        # Selecionar tipo com maior score
        best_project_type = max(project_type_scores.items(), key=lambda x: x[1])[0] if project_type_scores else ProjectType.WEB_APPLICATION
        
        # Detectar linguagem preferida
        language = self._detect_language_preference(goal_lower)
        
        # Recomendar framework baseado no contexto e linguagem
        recommended_frameworks = self._get_frameworks_for_language_and_type(language, best_project_type, goal_lower)
        
        # Detectar funcionalidades específicas
        features = self._detect_required_features(goal_lower)
        
        logger.info("Project goal analyzed",
                   project_type=best_project_type.value,
                   language=language,
                   frameworks=len(recommended_frameworks),
                   features=len(features))
        
        return {
            "project_type": best_project_type,
            "recommended_frameworks": recommended_frameworks,
            "language": language,
            "detected_features": features,
            "confidence": max(project_type_scores.values()) if project_type_scores else 0
        }
    
    def _detect_language_preference(self, goal: str) -> str:
        """Detecta preferência de linguagem no goal"""
        language_keywords = {
            "python": ["python", "flask", "django", "fastapi", "jupyter", "pandas", "py"],
            "javascript": ["javascript", "js", "react", "vue", "node", "express", "npm"],
            "typescript": ["typescript", "ts", "angular", "tsx"],
            "java": ["java", "spring", "maven", "gradle", "kotlin"],
            "csharp": ["c#", "csharp", ".net", "dotnet", "asp.net"],
            "go": ["go", "golang"],
            "rust": ["rust", "cargo"],
            "php": ["php", "laravel", "symfony", "composer"],
            "ruby": ["ruby", "rails", "gem"],
            "cpp": ["c++", "cpp", "cmake", "g++"],
            "c": ["c language", "gcc", "make"],
            "swift": ["swift", "ios", "xcode"],
            "dart": ["dart", "flutter"],
            "scala": ["scala", "sbt"],
            "elixir": ["elixir", "phoenix"],
            "html": ["html", "css", "static", "webpage"],
            "shell": ["bash", "shell", "script", "sh"]
        }
        
        for language, keywords in language_keywords.items():
            if any(keyword in goal for keyword in keywords):
                return language
        
        return "generic"  # Default - will be determined by project context
    
    def _get_frameworks_for_language_and_type(self, language: str, project_type: ProjectType, goal: str) -> List[Framework]:
        """Determina frameworks apropriados baseado na linguagem, tipo de projeto e contexto"""
        
        # Detectar frameworks específicos mencionados no goal
        framework_keywords = {
            "react": Framework.REACT,
            "vue": Framework.VUE,
            "angular": Framework.ANGULAR,
            "nextjs": Framework.NEXTJS,
            "express": Framework.EXPRESS,
            "flask": Framework.FLASK,
            "django": Framework.DJANGO,
            "fastapi": Framework.FASTAPI,
            "spring": Framework.VANILLA,  # Java Spring não está mapeado, usar VANILLA
            "rails": Framework.VANILLA,   # Ruby Rails não está mapeado, usar VANILLA
            "flutter": Framework.FLUTTER,
            "electron": Framework.ELECTRON,
            "streamlit": Framework.STREAMLIT,
            "dash": Framework.DASH
        }
        
        # Primeiro, verificar se algum framework foi mencionado explicitamente
        for keyword, framework in framework_keywords.items():
            if keyword in goal:
                return [framework]
        
        # Caso contrário, usar mapeamento baseado em linguagem e tipo
        language_framework_map = {
            "javascript": {
                ProjectType.WEB_APPLICATION: [Framework.REACT, Framework.VUE, Framework.NEXTJS],
                ProjectType.API_SERVICE: [Framework.EXPRESS],
                ProjectType.DESKTOP_APP: [Framework.ELECTRON],
                ProjectType.MOBILE_APP: [Framework.REACT_NATIVE]
            },
            "typescript": {
                ProjectType.WEB_APPLICATION: [Framework.REACT, Framework.ANGULAR, Framework.NEXTJS],
                ProjectType.API_SERVICE: [Framework.EXPRESS],
                ProjectType.DESKTOP_APP: [Framework.ELECTRON]
            },
            "python": {
                ProjectType.WEB_APPLICATION: [Framework.FLASK, Framework.DJANGO],
                ProjectType.API_SERVICE: [Framework.FASTAPI, Framework.FLASK, Framework.DJANGO],
                ProjectType.DATA_SCIENCE: [Framework.JUPYTER, Framework.STREAMLIT, Framework.DASH],
                ProjectType.DESKTOP_APP: [Framework.TKINTER]
            },
            "dart": {
                ProjectType.MOBILE_APP: [Framework.FLUTTER],
                ProjectType.WEB_APPLICATION: [Framework.FLUTTER]
            },
            "swift": {
                ProjectType.MOBILE_APP: [Framework.VANILLA]
            },
            "java": {
                ProjectType.API_SERVICE: [Framework.VANILLA],  # Spring Boot
                ProjectType.WEB_APPLICATION: [Framework.VANILLA],
                ProjectType.DESKTOP_APP: [Framework.VANILLA]
            }
        }
        
        frameworks = language_framework_map.get(language, {}).get(project_type, [Framework.VANILLA])
        return frameworks if frameworks else [Framework.VANILLA]
    
    def _detect_required_features(self, goal: str) -> List[str]:
        """Detecta funcionalidades específicas requeridas"""
        feature_keywords = {
            "authentication": ["auth", "login", "user", "authentication", "jwt"],
            "database": ["database", "db", "sql", "nosql", "mongodb", "postgresql"],
            "api": ["api", "rest", "graphql", "endpoint"],
            "frontend": ["frontend", "ui", "interface", "dashboard"],
            "testing": ["test", "testing", "unit test", "integration"],
            "deployment": ["deploy", "docker", "kubernetes", "aws", "cloud"],
            "security": ["security", "secure", "encryption", "ssl"],
            "monitoring": ["monitoring", "logs", "metrics", "observability"],
            "caching": ["cache", "redis", "memcached"],
            "messaging": ["queue", "messaging", "pubsub", "kafka"]
        }
        
        detected_features = []
        for feature, keywords in feature_keywords.items():
            if any(keyword in goal for keyword in keywords):
                detected_features.append(feature)
        
        return detected_features
    
    def generate_project_scaffold(self, 
                                goal: str,
                                project_name: str,
                                output_dir: str,
                                force_type: Optional[ProjectType] = None,
                                force_framework: Optional[Framework] = None) -> ProjectScaffold:
        """Gera scaffold completo do projeto"""
        
        # Analisar goal se não forçado
        if not force_type or not force_framework:
            analysis = self.analyze_project_goal(goal)
            project_type = force_type or analysis["project_type"]
            framework = force_framework or analysis["recommended_frameworks"][0]
        else:
            project_type = force_type
            framework = force_framework
            analysis = {"detected_features": []}
        
        # Buscar scaffold base
        scaffold_key = f"{project_type.value}_{framework.value}"
        base_scaffold = self.default_scaffolds.get(scaffold_key)
        
        if not base_scaffold:
            # Criar scaffold genérico
            base_scaffold = self._create_generic_scaffold(project_type, framework)
        
        # Customizar scaffold baseado no goal
        customized_scaffold = self._customize_scaffold(
            base_scaffold, 
            goal, 
            project_name, 
            analysis.get("detected_features", [])
        )
        
        logger.info("Project scaffold generated",
                   project_name=project_name,
                   type=project_type.value,
                   framework=framework.value,
                   features=len(analysis.get("detected_features", [])))
        
        return customized_scaffold
    
    def _create_generic_scaffold(self, project_type: ProjectType, framework: Framework) -> ProjectScaffold:
        """Cria scaffold genérico para combinação não mapeada"""
        return ProjectScaffold(
            name=f"Generic {project_type.value.title()} with {framework.value.title()}",
            description=f"Basic {project_type.value} project using {framework.value}",
            project_type=project_type,
            framework=framework,
            language="generic",  # Will be determined by context
            root_directory=DirectoryStructure(
                name="project",
                path=".",
                files=[
                    FileTemplate("README.md", "README.md", f"# {project_type.value.title()} Project\n\nGenerated with Evolux Engine\n\n## Getting Started\n\nThis is a generic project template. Add your implementation based on your chosen technology stack.\n")
                ]
            )
        )
    
    def _customize_scaffold(self, 
                          base_scaffold: ProjectScaffold, 
                          goal: str, 
                          project_name: str,
                          features: List[str]) -> ProjectScaffold:
        """Customiza scaffold baseado no goal e features"""
        
        # Criar cópia do scaffold
        customized = ProjectScaffold(
            name=project_name,
            description=f"{base_scaffold.description} - {goal}",
            project_type=base_scaffold.project_type,
            framework=base_scaffold.framework,
            language=base_scaffold.language,
            root_directory=base_scaffold.root_directory,
            dependencies=base_scaffold.dependencies.copy(),
            scripts=base_scaffold.scripts.copy(),
            env_vars=base_scaffold.env_vars.copy()
        )
        
        # Adicionar features específicas
        if "authentication" in features:
            self._add_auth_feature(customized)
        
        if "database" in features:
            self._add_database_feature(customized)
        
        if "testing" in features:
            self._add_testing_feature(customized)
        
        if "deployment" in features:
            self._add_deployment_feature(customized)
        
        return customized
    
    def _add_auth_feature(self, scaffold: ProjectScaffold):
        """Adiciona funcionalidade de autenticação"""
        if scaffold.language == "python":
            scaffold.dependencies.setdefault("python", []).extend([
                "flask-login", "werkzeug", "python-jose"
            ])
        elif scaffold.language == "javascript":
            scaffold.dependencies.setdefault("npm", []).extend([
                "jsonwebtoken", "bcryptjs", "passport"
            ])
        elif scaffold.language == "java":
            scaffold.dependencies.setdefault("maven", []).extend([
                "spring-security", "jwt"
            ])
    
    def _add_database_feature(self, scaffold: ProjectScaffold):
        """Adiciona funcionalidade de banco de dados"""
        if scaffold.language == "python":
            scaffold.dependencies.setdefault("python", []).extend([
                "sqlalchemy", "alembic"
            ])
        elif scaffold.language == "javascript":
            scaffold.dependencies.setdefault("npm", []).extend([
                "mongoose", "sequelize", "prisma"
            ])
        elif scaffold.language == "java":
            scaffold.dependencies.setdefault("maven", []).extend([
                "spring-data-jpa", "hibernate"
            ])
    
    def _add_testing_feature(self, scaffold: ProjectScaffold):
        """Adiciona funcionalidade de testes"""
        if scaffold.language == "python":
            scaffold.dependencies.setdefault("python", []).extend([
                "pytest", "pytest-cov"
            ])
            scaffold.scripts["test"] = "pytest tests/ --cov"
        elif scaffold.language == "javascript":
            scaffold.dependencies.setdefault("npm", []).extend([
                "jest", "mocha", "chai"
            ])
            scaffold.scripts["test"] = "npm test"
        elif scaffold.language == "java":
            scaffold.dependencies.setdefault("maven", []).extend([
                "junit", "mockito"
            ])
            scaffold.scripts["test"] = "mvn test"
    
    def _add_deployment_feature(self, scaffold: ProjectScaffold):
        """Adiciona funcionalidade de deployment"""
        # Adicionar Dockerfile
        dockerfile_content = self._get_dockerfile_template(scaffold.language)
        scaffold.root_directory.files.append(
            FileTemplate("Dockerfile", "Dockerfile", dockerfile_content)
        )
    
    def materialize_scaffold(self, scaffold: ProjectScaffold, output_dir: str) -> bool:
        """Materializa o scaffold no sistema de arquivos"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Variáveis para templates
            template_vars = {
                "project_name": scaffold.name,
                "description": scaffold.description,
                "project_type": scaffold.project_type.value,
                "framework": scaffold.framework.value,
                "language": scaffold.language,
                "timestamp": datetime.now().isoformat()
            }
            
            # Criar estrutura
            self._create_directory_structure(
                scaffold.root_directory, 
                output_path, 
                template_vars
            )
            
            # Criar arquivos de configuração adicionais
            self._create_config_files(scaffold, output_path, template_vars)
            
            logger.info("Project scaffold materialized",
                       project=scaffold.name,
                       output_dir=str(output_path),
                       files_created=self._count_files(scaffold.root_directory))
            
            return True
            
        except Exception as e:
            logger.error("Failed to materialize scaffold",
                        project=scaffold.name,
                        error=str(e))
            return False
    
    def _create_directory_structure(self, 
                                  directory: DirectoryStructure,
                                  base_path: Path,
                                  template_vars: Dict[str, Any]):
        """Cria estrutura de diretórios recursivamente"""
        
        current_path = base_path / directory.path if directory.path != "." else base_path
        current_path.mkdir(parents=True, exist_ok=True)
        
        # Criar arquivos
        for file_template in directory.files:
            file_path = current_path / file_template.name
            
            # Renderizar template se necessário
            if file_template.is_template:
                try:
                    template = self.jinja_env.from_string(file_template.content)
                    content = template.render(**template_vars, **file_template.variables)
                except Exception as e:
                    logger.warning("Template rendering failed, using raw content",
                                 file=file_template.name, error=str(e))
                    content = file_template.content
            else:
                content = file_template.content
            
            # Escrever arquivo
            file_path.write_text(content, encoding='utf-8')
            
            # Tornar executável se necessário
            if file_template.executable:
                file_path.chmod(0o755)
        
        # Criar subdiretórios
        for subdirectory in directory.subdirectories:
            self._create_directory_structure(subdirectory, base_path, template_vars)
    
    def _create_config_files(self, 
                           scaffold: ProjectScaffold,
                           output_path: Path,
                           template_vars: Dict[str, Any]):
        """Cria arquivos de configuração específicos"""
        
        # package.json para projetos Node.js
        if scaffold.language in ["javascript", "typescript"]:
            package_json = {
                "name": scaffold.name.lower().replace(" ", "-"),
                "version": "1.0.0",
                "description": scaffold.description,
                "scripts": scaffold.scripts,
                "dependencies": scaffold.dependencies.get("npm", {}),
                "devDependencies": {}
            }
            
            (output_path / "package.json").write_text(
                json.dumps(package_json, indent=2),
                encoding='utf-8'
            )
        
        # requirements.txt para projetos Python
        if scaffold.language == "python" and scaffold.dependencies.get("python"):
            requirements = "\n".join(scaffold.dependencies["python"]) + "\n"
            (output_path / "requirements.txt").write_text(requirements, encoding='utf-8')
        
        # .env se existem variáveis
        if scaffold.env_vars:
            env_content = "\n".join(f"{k}={v}" for k, v in scaffold.env_vars.items()) + "\n"
            (output_path / ".env").write_text(env_content, encoding='utf-8')
    
    def _count_files(self, directory: DirectoryStructure) -> int:
        """Conta total de arquivos na estrutura"""
        count = len(directory.files)
        for subdir in directory.subdirectories:
            count += self._count_files(subdir)
        return count
    
    # Template content methods (simplified for brevity)
    def _get_flask_app_template(self) -> str:
        return """from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
"""
    
    def _get_flask_config_template(self) -> str:
        return """import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
"""
    
    def _get_readme_template(self, project_type: str) -> str:
        return f"""# {{{{ project_name }}}}

{{{{ description }}}}

## Description

This is a {project_type} generated by Evolux Engine.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## Features

- Modern architecture
- Best practices implementation
- Ready for development
- Comprehensive testing setup

## Generated by Evolux Engine

This project was automatically generated and scaffolded by Evolux Engine AI orchestration platform.
"""
    
    def _get_python_gitignore(self) -> str:
        return """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.idea/
.vscode/
*.log
"""
    
    def _get_node_gitignore(self) -> str:
        return """node_modules/
.npm
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
lerna-debug.log*
dist
dist-ssr
*.local
.vite
.idea/
.vscode/
*.log
"""
    
    # Additional template methods would be implemented here...
    def _get_flask_models_template(self) -> str:
        return "# Database models will be defined here\n"
    
    def _get_flask_routes_template(self) -> str:
        return "# Application routes will be defined here\n"
    
    def _get_flask_test_template(self) -> str:
        return "# Tests will be defined here\n"
    
    def _get_flask_base_template(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ project_name }}</title>
</head>
<body>
    <h1>{{ project_name }}</h1>
    {% block content %}{% endblock %}
</body>
</html>"""
    
    def _get_flask_index_template(self) -> str:
        return """{% extends "base.html" %}
{% block content %}
<p>Welcome to your Flask application!</p>
{% endblock %}"""
    
    def _get_fastapi_main_template(self) -> str:
        return """from fastapi import FastAPI

app = FastAPI(title="{{ project_name }}", description="{{ description }}")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
"""
    
    def _get_fastapi_models_template(self) -> str:
        return "# Database models will be defined here\n"
    
    def _get_fastapi_schemas_template(self) -> str:
        return "# Pydantic schemas will be defined here\n"
    
    def _get_fastapi_crud_template(self) -> str:
        return "# CRUD operations will be defined here\n"
    
    def _get_fastapi_database_template(self) -> str:
        return "# Database configuration will be defined here\n"
    
    def _get_fastapi_router_template(self) -> str:
        return """from fastapi import APIRouter

router = APIRouter()

@router.get("/items/")
async def read_items():
    return [{"item_id": "1", "name": "Item 1"}]
"""
    
    def _get_fastapi_test_template(self) -> str:
        return "# Tests will be defined here\n"
    
    def _get_react_package_template(self) -> str:
        return """{
  "name": "{{ project_name.lower().replace(' ', '-') }}",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@vitejs/plugin-react": "^4.0.3",
    "typescript": "^5.0.2",
    "vite": "^4.4.5"
  }
}"""
    
    def _get_react_tsconfig_template(self) -> str:
        return """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}"""
    
    def _get_react_vite_config_template(self) -> str:
        return """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})"""
    
    def _get_react_index_template(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{ project_name }}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>"""
    
    def _get_react_main_template(self) -> str:
        return """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './App.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)"""
    
    def _get_react_app_template(self) -> str:
        return """import React from 'react'
import './App.css'

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>{{ project_name }}</h1>
        <p>{{ description }}</p>
      </header>
    </div>
  )
}

export default App"""
    
    def _get_react_css_template(self) -> str:
        return """.App {
  text-align: center;
}

.App-header {
  padding: 20px;
  color: #333;
}"""
    
    def _get_dockerfile_template(self, language: str) -> str:
        templates = {
            "python": """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]""",
            
            "javascript": """FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]""",
            
            "typescript": """FROM node:18-alpine

WORKDIR /app

COPY package*.json tsconfig.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]""",
            
            "java": """FROM openjdk:17-jre-slim

WORKDIR /app

COPY target/*.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]""",
            
            "go": """FROM golang:1.19-alpine AS builder

WORKDIR /app
COPY . .
RUN go mod download
RUN go build -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .

EXPOSE 8080

CMD ["./main"]""",
            
            "rust": """FROM rust:1.70 AS builder

WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=builder /app/target/release/app .

EXPOSE 8080

CMD ["./app"]"""
        }
        
        return templates.get(language, templates["javascript"])  # Default to Node.js