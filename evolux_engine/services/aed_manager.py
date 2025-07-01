# evolux_engine/services/aed_manager.py
import docker
import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuração do logging estruturado
logging.basicConfig(level=logging.INFO, format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')

WORKSPACE_PATH = "/home/app/evolux/project_workspaces"
DOCKER_NETWORK = "evolux_bridge_network"
BASE_DOMAIN = "aed.localhost"

class AEDTriggerHandler(FileSystemEventHandler):
    """Manipulador de eventos que dispara a criação de um AED."""

    def __init__(self, docker_client):
        self.docker_client = docker_client

    def on_created(self, event):
        # O gatilho é um arquivo chamado ".aed_deploy"
        if not event.is_directory and os.path.basename(event.src_path) == '.aed_deploy':
            project_dir = os.path.dirname(event.src_path)
            project_name = os.path.basename(project_dir)
            logging.info(f"Gatilho AED detectado para o projeto: {project_name}")
            self.deploy_aed(project_dir, project_name)

    def deploy_aed(self, project_dir, project_name):
        """Constrói e implanta um container para o projeto."""
        try:
            image_tag = f"aed-{project_name.lower()}:latest"
            logging.info(f"Iniciando build da imagem {image_tag} a partir de {project_dir}")

            # Constrói a imagem
            image, build_logs = self.docker_client.images.build(
                path=project_dir,
                tag=image_tag,
                rm=True # Remove containers intermediários
            )
            for log in build_logs:
                if 'stream' in log:
                    logging.info(log['stream'].strip())

            logging.info(f"Build da imagem {image_tag} concluído com sucesso.")

            # Define as labels para o Traefik e o gerenciamento do ciclo de vida
            container_name = f"aed-{project_name.lower()}-{int(time.time())}"
            labels = {
                "traefik.enable": "true",
                f"traefik.http.routers.{container_name}.rule": f"Host(`{project_name.lower()}.{BASE_DOMAIN}`)",
                "evolux.aed.managed": "true", # Label para identificar nossos containers
                "evolux.aed.project_name": project_name,
                "evolux.aed.creation_timestamp": str(int(time.time()))
            }

            # Roda o container com recursos limitados
            container = self.docker_client.containers.run(
                image=image_tag,
                name=container_name,
                labels=labels,
                network=DOCKER_NETWORK,
                detach=True,
                mem_limit="256m", # Limite de memória
                cpu_shares=512    # Prioridade de CPU relativa (1024 é o padrão)
            )

            access_url = f"http://{project_name.lower()}.{BASE_DOMAIN}"
            logging.info(f"AED '{project_name}' implantado com sucesso. Acesso em: {access_url}")
            
            # Opcional: remover o arquivo de gatilho para evitar re-deploy
            os.remove(os.path.join(project_dir, '.aed_deploy'))

        except docker.errors.BuildError as e:
            logging.error(f"Erro no build do AED para '{project_name}': {e}")
        except docker.errors.APIError as e:
            logging.error(f"Erro na API do Docker para '{project_name}': {e}")


def start_aed_monitoring():
    """Inicia o monitoramento do workspace."""
    logging.info("Iniciando o serviço de monitoramento de AED...")
    client = docker.from_env()
    event_handler = AEDTriggerHandler(client)
    observer = Observer()
    observer.schedule(event_handler, WORKSPACE_PATH, recursive=True)
    observer.start()
    
    try:
        while True:
            # TODO: Adicionar lógica de cleanup de AEDs inativos aqui
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Este script seria chamado a partir do run.py do evolux-core
# if __name__ == "__main__":
#     start_aed_monitoring()
