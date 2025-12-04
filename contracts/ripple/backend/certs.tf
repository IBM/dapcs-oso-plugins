// Copyright (c) 2025 IBM Corp.
// All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

# org ca cert used to sign everything
resource "tls_private_key" "grep11_ca_private_key" {
  algorithm = "RSA"
}

resource "tls_self_signed_cert" "grep11_ca_cert" {
  private_key_pem = tls_private_key.grep11_ca_private_key.private_key_pem

  is_ca_certificate = true

  subject {
    common_name  = "dap.local"
    country      = "US"
    organization = "HPS"
  }

  validity_period_hours = var.CERT_VALIDITY_PERIOD

  allowed_uses = [
    "digital_signature",
    "cert_signing",
    "crl_signing",
  ]
}

resource "tls_private_key" "server_key" {
  algorithm = "RSA"
}

resource "tls_cert_request" "server_cert" {
  private_key_pem = tls_private_key.server_key.private_key_pem

  dns_names = ["localhost", "ep11server"]

  subject {
    common_name  = "grep11-c16.control23.dap.local"
    organization = "HPS"
    country      = "US"
  }
}

resource "tls_locally_signed_cert" "server_cert" {
  // CA certificate for product
  ca_cert_pem = tls_self_signed_cert.grep11_ca_cert.cert_pem

  // CSR for service
  cert_request_pem = tls_cert_request.server_cert.cert_request_pem
  // CA Private key for service
  ca_private_key_pem = tls_private_key.grep11_ca_private_key.private_key_pem

  validity_period_hours = var.CERT_VALIDITY_PERIOD

  allowed_uses = [
    "digital_signature",
    "key_encipherment",
    "server_auth",
  ]
}

resource "tls_private_key" "client_key" {
  algorithm = "RSA"
}

resource "tls_cert_request" "client_cert" {
  private_key_pem = tls_private_key.client_key.private_key_pem

  subject {
    common_name  = "client"
    organization = "HPS"
    country      = "US"
  }
}

resource "tls_locally_signed_cert" "client_cert" {
  // CA certificate for product
  ca_cert_pem = tls_self_signed_cert.grep11_ca_cert.cert_pem

  // CSR for service
  cert_request_pem = tls_cert_request.client_cert.cert_request_pem
  // CA Private key for service
  ca_private_key_pem = tls_private_key.grep11_ca_private_key.private_key_pem

  validity_period_hours = var.CERT_VALIDITY_PERIOD

  allowed_uses = [
    "digital_signature",
    "key_encipherment",
    "client_auth",
  ]
}
