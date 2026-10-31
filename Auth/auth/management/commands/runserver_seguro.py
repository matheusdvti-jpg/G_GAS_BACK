import ssl

from django.core.management.commands.runserver import Command as RunserverCommand
from django.core.servers.basehttp import WSGIServer

from ggas.certificado import garantir_certificado
from ggas.preparar import preparar_banco


class ServidorTLS(WSGIServer):
    def server_bind(self):
        super().server_bind()
        certificado, chave = garantir_certificado()
        contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        contexto.minimum_version = ssl.TLSVersion.TLSv1_2
        contexto.load_cert_chain(certificado, chave)
        self.socket = contexto.wrap_socket(self.socket, server_side=True)


class Command(RunserverCommand):
    help = 'Sobe a API só em HTTPS, em 127.0.0.1:8443.'
    default_port = '8443'
    server_cls = ServidorTLS

    def handle(self, *args, **options):
        garantir_certificado()
        preparar_banco()
        if not options.get('addrport'):
            options['addrport'] = '127.0.0.1:8443'
        super().handle(*args, **options)
