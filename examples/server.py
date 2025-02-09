import aiofiles
from aiohttp import web
import json
import ssl
import os
import sys
from OpenSSL import crypto

SAMPLE_FILES = os.path.join("samples", "running")
CERT_FILE = "selfsigned.crt"
KEY_FILE = "private.key"

routes = web.RouteTableDef()


@routes.post("/api/login/Basic")
async def login(request):
    await request.post()

    response = web.json_response(
        {
            "firstname": "firstname",
            "lastname": "lastname",
            "token": "token",
            "roles": ["Home_Owner"],
            "loginTime": "loginTime",
        }
    )

    response.set_cookie("AuthCookie", "blah")

    return response


@routes.get("/api/{api:.*}")
async def api(request):
    if "AuthCookie" not in request.cookies:
        raise web.HTTPUnauthorized()

    filename = f"{request.match_info['api'].replace('/', '.')}.json"
    path = os.path.join(SAMPLE_FILES, filename)

    async with aiofiles.open(path, mode="r") as f:
        body = await f.read()

    return web.json_response(json.loads(body))


async def make_app():
    app = web.Application()
    app.add_routes(routes)
    return app


def create_self_signed_cert():
    emailAddress = "emailAddress"
    commonName = "commonName"
    countryName = "NT"
    localityName = "localityName"
    stateOrProvinceName = "stateOrProvinceName"
    organizationName = "organizationName"
    organizationUnitName = "organizationUnitName"
    serialNumber = 0
    validityStartInSeconds = 0
    validityEndInSeconds = 10 * 365 * 24 * 60 * 60
    # create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)
    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = countryName
    cert.get_subject().ST = stateOrProvinceName
    cert.get_subject().L = localityName
    cert.get_subject().O = organizationName
    cert.get_subject().OU = organizationUnitName
    cert.get_subject().CN = commonName
    cert.get_subject().emailAddress = emailAddress
    cert.set_serial_number(serialNumber)
    cert.gmtime_adj_notBefore(validityStartInSeconds)
    cert.gmtime_adj_notAfter(validityEndInSeconds)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, "sha512")
    with open(CERT_FILE, "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
    with open(KEY_FILE, "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8"))


if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
    create_self_signed_cert()

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(CERT_FILE, KEY_FILE)

if not os.path.exists(SAMPLE_FILES):
    print(f"Missing sample files in {SAMPLE_FILES}, create them:")
    print(
        "curl -o getsamples.sh https://raw.githubusercontent.com/vloschiavo/powerwall2/master/scripts/getsamples.sh"
    )
    print("chmod u+x getsamples.sh")
    print("./getsamples.sh youraddress youremail yourpass .server/samples")
    sys.exit(-1)

web.run_app(make_app(), ssl_context=ssl_context)
