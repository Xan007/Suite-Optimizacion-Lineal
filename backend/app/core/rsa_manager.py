import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from app.core.logger import logger


class RSAManager:
    """Maneja la generación y carga de claves RSA."""

    def __init__(self, private_key_path: str, public_key_path: str):
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path

        # Cargar o generar claves
        if self._keys_exist():
            self._load_keys()
        else:
            self._generate_keys()

    def _keys_exist(self) -> bool:
        """Verifica si los archivos de claves existen."""
        return os.path.exists(self.private_key_path) and os.path.exists(
            self.public_key_path
        )

    def _generate_keys(self) -> None:
        """Genera un par de claves RSA."""
        logger.info("Generando nuevo par de claves RSA...")

        # Generar clave privada
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )

        # Serializar clave privada
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Serializar clave pública
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Guardar archivos
        os.makedirs(os.path.dirname(self.private_key_path), exist_ok=True)
        with open(self.private_key_path, "wb") as f:
            f.write(private_pem)

        os.makedirs(os.path.dirname(self.public_key_path), exist_ok=True)
        with open(self.public_key_path, "wb") as f:
            f.write(public_pem)

        logger.info(f"Claves generadas en {self.private_key_path} y {self.public_key_path}")
        self._load_keys()

    def _load_keys(self) -> None:
        """Carga las claves desde archivos."""
        with open(self.private_key_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )

        with open(self.public_key_path, "rb") as f:
            self.public_key = serialization.load_pem_public_key(
                f.read(), backend=default_backend()
            )

        logger.info("Claves RSA cargadas correctamente")

    def get_public_key_pem(self) -> str:
        """Retorna la clave pública en formato PEM como string."""
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return public_pem.decode()

    def decrypt(self, encrypted_data: bytes) -> str:
        """Descifra datos usando la clave privada RSA."""
        from cryptography.hazmat.primitives.asymmetric import padding

        decrypted = self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=serialization.Encoding.PEM),
                algorithm=serialization.Encoding.PEM,
                label=None,
            ),
        )
        return decrypted.decode()
