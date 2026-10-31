import datetime
import ipaddress
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.conf import settings


def diretorio():
    pasta = Path(settings.BASE_DIR) / 'certs'
    pasta.mkdir(exist_ok=True)
    return pasta


def garantir_certificado():
    pasta = diretorio()
    certificado = pasta / 'localhost.crt'
    chave = pasta / 'localhost.key'
    if certificado.exists() and chave.exists():
        return certificado, chave

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
    agora = datetime.datetime.now(datetime.timezone.utc)
    alt = x509.SubjectAlternativeName(
        [
            x509.DNSName('localhost'),
            x509.IPAddress(ipaddress.ip_address('127.0.0.1')),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora)
        .not_valid_after(agora + datetime.timedelta(days=825))
        .add_extension(alt, critical=False)
        .sign(key, hashes.SHA256())
    )
    chave.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    certificado.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return certificado, chave
