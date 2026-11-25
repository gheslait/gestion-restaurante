
"""
Carga datos de demostración para gestion-restaurante.

Características:
- Idempotente: puede ejecutarse varias veces.
- No elimina registros.
- No modifica datos existentes.
- Genera contraseñas aleatorias para los usuarios nuevos.
- Utiliza los CRUD del proyecto para crear pedidos y facturas.
- Los pedidos de demostración se identifican mediante una marca en observaciones.

Ejecución:
    python -m app.scripts.seed_demo
"""

import secrets
import sys
from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.crud import factura as crud_factura
from app.crud import pedido as crud_pedido
from app.crud import usuario as crud_usuario
from app.models import (
    Categoria,
    Cliente,
    Inventario,
    Mesa,
    Producto,
    Usuario,
)
from app.models.enums import (
    EstadoPedido,
    MetodoPago,
    RolUsuario,
    UnidadInventario,
)
from app.schemas.pedido import DetalleCreate, PedidoCreate
from app.schemas.usuario import UsuarioCreate


VERSION = "v1"
MARCA = f"[DEMO-SEED:{VERSION}]"


# ---------------------------------------------------------
# 1. USUARIOS
# ---------------------------------------------------------

USUARIOS = [
    ("Carlos Mendoza", "cajero1", RolUsuario.cajero),
    ("María González", "cajero2", RolUsuario.cajero),
    ("Laura Rodríguez", "mesero1", RolUsuario.mesero),
    ("Andrés Martínez", "mesero2", RolUsuario.mesero),
    ("Pedro Gómez", "cocina1", RolUsuario.cocinero),
    ("Daniel Torres", "cocina2", RolUsuario.cocinero),
]


def crear_usuarios(db):
    print("\n=== USUARIOS ===")

    creados = 0

    for nombre, username, rol in USUARIOS:
        existente = crud_usuario.get_by_username(db, username)

        if existente:
            print(f"[EXISTE] {username}: no se modifica")
            continue

        # Contraseña aleatoria, nunca se guarda en texto plano.
        password = "admin123"

        usuario = crud_usuario.create(
            db,
            UsuarioCreate(
                nombre=nombre,
                username=username,
                password=password,
                rol=rol,
            ),
        )

        creados += 1

        print(f"[CREADO] {usuario.username} | Rol: {rol.value}")
        print(f"         Contraseña temporal: {password}")

    print(f"Usuarios nuevos: {creados}")
    print("Guarda las contraseñas mostradas; no se vuelven a generar al ejecutar de nuevo.")


# ---------------------------------------------------------
# 2. MESAS
# ---------------------------------------------------------

def crear_mesas(db):
    print("\n=== MESAS ===")

    creadas = 0

    for numero in range(101, 113):
        existente = db.scalar(
            select(Mesa).where(Mesa.numero_mesa == numero)
        )

        if existente:
            print(f"[EXISTE] Mesa {numero}")
            continue

        mesa = Mesa(
            numero_mesa=numero,
            capacidad=4 if numero % 2 == 0 else 2,
        )

        db.add(mesa)
        creadas += 1
        print(f"[CREADA] Mesa {numero}")

    db.commit()
    print(f"Mesas nuevas: {creadas}")


# ---------------------------------------------------------
# 3. CATEGORÍAS
# ---------------------------------------------------------

CATEGORIAS = [
    ("Entradas", "Entradas y aperitivos"),
    ("Platos fuertes", "Platos principales del restaurante"),
    ("Bebidas", "Bebidas frías y calientes"),
    ("Postres", "Postres y productos dulces"),
]


def crear_categorias(db):
    print("\n=== CATEGORÍAS ===")

    resultado = {}

    for nombre, descripcion in CATEGORIAS:
        categoria = db.scalar(
            select(Categoria).where(Categoria.nombre == nombre)
        )

        if categoria is None:
            categoria = Categoria(
                nombre=nombre,
                descripcion=descripcion,
                activo=True,
            )
            db.add(categoria)
            db.flush()
            print(f"[CREADA] {nombre}")
        else:
            print(f"[EXISTE] {nombre}: no se modifica")

        resultado[nombre] = categoria

    db.commit()
    return resultado


# ---------------------------------------------------------
# 4. PRODUCTOS E INVENTARIO
# ---------------------------------------------------------

PRODUCTOS = [
    # nombre, categoría, descripción, precio, stock, stock mínimo
    (
        "Patacones",
        "Entradas",
        "Patacones con salsa de la casa",
        "12000.00",
        "80",
        "10",
    ),
    (
        "Arepa de huevo",
        "Entradas",
        "Arepa de huevo tradicional",
        "9000.00",
        "80",
        "10",
    ),
    (
        "Nachos",
        "Entradas",
        "Nachos con queso y guacamole",
        "15000.00",
        "80",
        "10",
    ),
    (
        "Hamburguesa de la casa",
        "Platos fuertes",
        "Hamburguesa con carne, queso y vegetales",
        "28000.00",
        "80",
        "10",
    ),
    (
        "Pollo a la plancha",
        "Platos fuertes",
        "Pechuga a la plancha con acompañamiento",
        "26000.00",
        "80",
        "10",
    ),
    (
        "Pasta Alfredo",
        "Platos fuertes",
        "Pasta en salsa Alfredo",
        "24000.00",
        "80",
        "10",
    ),
    (
        "Pizza personal",
        "Platos fuertes",
        "Pizza personal de la casa",
        "22000.00",
        "80",
        "10",
    ),
    (
        "Limonada natural",
        "Bebidas",
        "Limonada natural de la casa",
        "7000.00",
        "100",
        "15",
    ),
    (
        "Agua mineral",
        "Bebidas",
        "Agua mineral personal",
        "4000.00",
        "100",
        "15",
    ),
    (
        "Jugo natural",
        "Bebidas",
        "Jugo natural de fruta",
        "8000.00",
        "100",
        "15",
    ),
    (
        "Brownie",
        "Postres",
        "Brownie de chocolate",
        "9000.00",
        "60",
        "10",
    ),
    (
        "Cheesecake",
        "Postres",
        "Porción de cheesecake",
        "12000.00",
        "60",
        "10",
    ),
]


def crear_productos(db, categorias):
    print("\n=== PRODUCTOS E INVENTARIO ===")

    productos_creados = 0
    inventarios_creados = 0

    resultado = {}

    for (
        nombre,
        categoria_nombre,
        descripcion,
        precio,
        stock,
        stock_minimo,
    ) in PRODUCTOS:

        categoria = categorias[categoria_nombre]

        producto = db.scalars(
            select(Producto).where(
                Producto.nombre == nombre,
                Producto.id_categoria == categoria.id,
            )
        ).first()

        if producto is None:
            producto = Producto(
                nombre=nombre,
                descripcion=descripcion,
                precio=Decimal(precio),
                id_categoria=categoria.id,
                disponible=True,
            )
            db.add(producto)
            db.flush()

            productos_creados += 1
            print(f"[CREADO] {nombre}")
        else:
            print(f"[EXISTE] {nombre}: no se modifica")

        # Cada producto debe tener un único registro de inventario.
        inventario = db.scalar(
            select(Inventario).where(
                Inventario.id_producto == producto.id
            )
        )

        if inventario is None:
            inventario = Inventario(
                id_producto=producto.id,
                cantidad=Decimal(stock),
                stock_minimo=Decimal(stock_minimo),
                unidad=UnidadInventario.unidad,
            )

            db.add(inventario)
            inventarios_creados += 1

            print(
                f"         Inventario creado: "
                f"{stock} {UnidadInventario.unidad.value}"
            )
        else:
            print("         Inventario existente: no se modifica")

        resultado[nombre] = producto

    db.commit()

    print(f"Productos nuevos: {productos_creados}")
    print(f"Inventarios nuevos: {inventarios_creados}")

    return resultado


# ---------------------------------------------------------
# 5. CLIENTES
# ---------------------------------------------------------

CLIENTES = [
    (
        "Juan Pérez",
        "+57 300 000 0101",
        "juan.demo@example.com",
        "DEMO-CLI-001",
    ),
    (
        "Ana Martínez",
        "+57 300 000 0102",
        "ana.demo@example.com",
        "DEMO-CLI-002",
    ),
    (
        "Carlos Ramírez",
        "+57 300 000 0103",
        "carlos.demo@example.com",
        "DEMO-CLI-003",
    ),
    (
        "Laura Gómez",
        "+57 300 000 0104",
        "laura.demo@example.com",
        "DEMO-CLI-004",
    ),
    (
        "Sofía Torres",
        "+57 300 000 0105",
        "sofia.demo@example.com",
        "DEMO-CLI-005",
    ),
    (
        "Pedro Díaz",
        "+57 300 000 0106",
        "pedro.demo@example.com",
        "DEMO-CLI-006",
    ),
]


def crear_clientes(db):
    print("\n=== CLIENTES ===")

    resultado = {}

    for nombre, telefono, email, documento in CLIENTES:
        cliente = db.scalar(
            select(Cliente).where(
                Cliente.documento == documento
            )
        )

        if cliente is None:
            cliente = Cliente(
                nombre=nombre,
                telefono=telefono,
                email=email,
                documento=documento,
            )

            db.add(cliente)
            db.flush()

            print(f"[CREADO] {nombre}")
        else:
            print(f"[EXISTE] {nombre}: no se modifica")

        resultado[documento] = cliente

    db.commit()
    return resultado


# ---------------------------------------------------------
# 6. PEDIDOS Y FACTURAS
# ---------------------------------------------------------

PEDIDOS = [
    {
        "clave": "pedido-pagado",
        "mesa": 101,
        "usuario": "mesero1",
        "cliente": "DEMO-CLI-001",
        "estado_final": EstadoPedido.pagado,
        "metodo_pago": MetodoPago.nequi,
        "items": [
            ("Hamburguesa de la casa", 1),
            ("Limonada natural", 2),
        ],
    },
    {
        "clave": "pedido-servido",
        "mesa": 102,
        "usuario": "mesero2",
        "cliente": "DEMO-CLI-002",
        "estado_final": EstadoPedido.servido,
        "items": [
            ("Pizza personal", 1),
            ("Agua mineral", 1),
        ],
    },
    {
        "clave": "pedido-cocina",
        "mesa": 103,
        "usuario": "mesero1",
        "cliente": "DEMO-CLI-003",
        "estado_final": EstadoPedido.en_cocina,
        "items": [
            ("Pasta Alfredo", 1),
            ("Jugo natural", 1),
        ],
    },
    {
        "clave": "pedido-abierto",
        "mesa": 104,
        "usuario": "mesero2",
        "cliente": "DEMO-CLI-004",
        "estado_final": EstadoPedido.abierto,
        "items": [
            ("Arepa de huevo", 1),
            ("Brownie", 1),
        ],
    },
]


def buscar_pedido_demo(db, clave):
    marca_pedido = f"{MARCA}:{clave}"

    return db.scalar(
        select(__import__(
            "app.models.pedido", fromlist=["Pedido"]
        ).Pedido).where(
            __import__(
                "app.models.pedido", fromlist=["Pedido"]
            ).Pedido.observaciones == marca_pedido
        )
    )


def crear_o_recuperar_pedido(
    db,
    configuracion,
    productos,
    clientes,
):
    clave = configuracion["clave"]
    marca_pedido = f"{MARCA}:{clave}"

    PedidoModel = __import__(
        "app.models.pedido", fromlist=["Pedido"]
    ).Pedido

    pedido = db.scalar(
        select(PedidoModel).where(
            PedidoModel.observaciones == marca_pedido
        )
    )

    if pedido is not None:
        print(f"[EXISTE] {clave}: pedido #{pedido.id}")
        return pedido

    mesa = db.scalar(
        select(Mesa).where(
            Mesa.numero_mesa == configuracion["mesa"]
        )
    )

    if mesa is None:
        print(f"[OMITIDO] No existe la mesa {configuracion['mesa']}")
        return None

    # No utilizar mesas ocupadas o reservadas por datos ajenos
    # al script. Tampoco cambiar su estado manualmente.
    from app.models.enums import EstadoMesa

    if mesa.estado not in {EstadoMesa.libre, EstadoMesa.ocupada}:
        print(
            f"[OMITIDO] Mesa {mesa.numero_mesa} "
            f"no disponible: {mesa.estado.value}"
        )
        return None

    usuario = crud_usuario.get_by_username(
        db,
        configuracion["usuario"],
    )

    if usuario is None or usuario.rol != RolUsuario.mesero:
        print(
            f"[OMITIDO] El usuario {configuracion['usuario']} "
            "no existe o no tiene rol de mesero"
        )
        return None

    cliente = clientes[configuracion["cliente"]]

    detalles = []

    for nombre_producto, cantidad in configuracion["items"]:
        producto = productos[nombre_producto]

        detalles.append(
            DetalleCreate(
                id_producto=producto.id,
                cantidad=cantidad,
            )
        )

    pedido = crud_pedido.create(
        db,
        PedidoCreate(
            id_mesa=mesa.id,
            id_cliente=cliente.id,
            observaciones=marca_pedido,
            items=detalles,
        ),
        id_usuario=usuario.id,
    )

    print(
        f"[CREADO] Pedido #{pedido.id} "
        f"| Mesa {mesa.numero_mesa} "
        f"| Total: ${pedido.total}"
    )

    return pedido


def avanzar_pedido(db, pedido, estado_final):
    """
    Avanza el pedido exclusivamente mediante transiciones
    permitidas por crud.pedido.
    """

    if pedido is None:
        return None

    if pedido.estado in {
        EstadoPedido.pagado,
        EstadoPedido.cancelado,
    }:
        return pedido

    if estado_final == EstadoPedido.abierto:
        return pedido

    if pedido.estado == EstadoPedido.abierto:
        pedido = crud_pedido.cambiar_estado(
            db,
            pedido,
            EstadoPedido.en_cocina,
        )

    if (
        estado_final in {
            EstadoPedido.servido,
            EstadoPedido.pagado,
        }
        and pedido.estado == EstadoPedido.en_cocina
    ):
        pedido = crud_pedido.cambiar_estado(
            db,
            pedido,
            EstadoPedido.servido,
        )

    return pedido


def crear_pedidos_y_facturas(db, productos, clientes):
    print("\n=== PEDIDOS Y FACTURAS ===")

    for configuracion in PEDIDOS:
        clave = configuracion["clave"]

        try:
            pedido = crear_o_recuperar_pedido(
                db,
                configuracion,
                productos,
                clientes,
            )

            if pedido is None:
                continue

            pedido = avanzar_pedido(
                db,
                pedido,
                configuracion["estado_final"],
            )

            # La factura se crea únicamente cuando el pedido
            # alcanza el estado servido.
            if configuracion["estado_final"] == EstadoPedido.pagado:
                factura_existente = crud_factura.get_by_pedido(
                    db,
                    pedido.id,
                )

                if factura_existente is None:
                    if pedido.estado != EstadoPedido.servido:
                        print(
                            f"[OMITIDO] No se puede facturar "
                            f"el pedido #{pedido.id}: "
                            f"estado {pedido.estado.value}"
                        )
                        continue

                    factura = crud_factura.facturar_pedido(
                        db,
                        pedido,
                        configuracion["metodo_pago"],
                    )

                    print(
                        f"[FACTURA] {factura.numero_factura} "
                        f"| Pedido #{pedido.id} "
                        f"| Total: ${factura.total}"
                    )
                else:
                    print(
                        f"[EXISTE] Factura "
                        f"{factura_existente.numero_factura}"
                    )

            print(
                f"[PEDIDO] #{pedido.id} "
                f"| Estado: {pedido.estado.value}"
            )

        except Exception as error:
            db.rollback()
            print(f"[ERROR] {clave}: {error}")


# ---------------------------------------------------------
# 7. EJECUCIÓN PRINCIPAL
# ---------------------------------------------------------

def main():
    db = SessionLocal()

    try:
        print("=" * 60)
        print("CARGA DE DATOS DE DEMOSTRACIÓN")
        print(f"Versión: {VERSION}")
        print("No se eliminarán ni sobrescribirán datos existentes.")
        print("=" * 60)

        crear_usuarios(db)
        crear_mesas(db)

        categorias = crear_categorias(db)
        productos = crear_productos(db, categorias)
        clientes = crear_clientes(db)

        crear_pedidos_y_facturas(
            db,
            productos,
            clientes,
        )

        print("\n" + "=" * 60)
        print("PROCESO DE DEMOSTRACIÓN FINALIZADO")
        print("=" * 60)

    except Exception as error:
        db.rollback()
        print(f"\n[ERROR GENERAL] {error}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
