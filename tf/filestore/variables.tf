variable "AWS_PROFILE" {
  type = map(string)

  default = {
    dev = "default"
    prod = "default"
  }
}
variable "AWS_REGION" {
    type = map(string)

    default = {
        dev = "ap-northeast-2"
        prod = "ap-northeast-2"
    }
}

variable "LOCAL_FQDN" {
    type = map(string)

    default = {
        dev = "our4000.iptime.org"
        prod = "our4000.iptime.org"
    }
}

variable "ROOT_FQDN" {
    type = map(string)

    default = {
        dev = "apocrypha.in"
        prod = "apocrypha.in"
    }
}

variable "API_FQDN" {
    type = map(string)

    default = {
        dev = "api-dev.apocrypha.in"
        prod = "api.apocrypha.in"
    }
}

variable "MEDIA_CDN_FQDN" {
    type = map(string)

    default = {
        dev = "cdn-dev.apocrypha.in"
        prod = "cdn.apocrypha.in"
    }
}

variable "CONSOLE_FQDN" {
    type = map(string)

    default = {
        dev = "console-dev.apocrypha.in"
        prod = "console.apocrypha.in"
    }
}

variable "MB_NAME" {
    type = map(string)

    default = {
        dev = "dev-apocrypha-mb"
        prod = "apocrypha-mb"
    }
}

variable "API_SERVER_IMAGE_NAME" {
    type = map(string)

    default = {
        dev = "dev-apocrypha-api"
        prod = "apocrypha-api"
    }
}

variable "SERVICE_PREFIX" {
    type = map(string)

    default = {
        dev = "dev-apocrypha"
        prod = "apocrypha"
    }
}

variable "MUQ_NAME" {
    type = map(string)

    default = {
        dev = "dev-apocrypha-muq"
        prod = "apocrypha-muq"
    }
}

variable "MUQ_VT" {
    type = map(string)

    default = {
        dev = "10"
        prod = "10"
    }
}

variable "MUQ_MR" {
    type = map(string)

    default = {
        dev = "345600"
        prod = "345600"
    }
}

variable "MUQ_RW" {
    type = map(string)

    default = {
        dev = "20"
        prod = "20"
    }
}

variable "MB_INPUT_PREFIX" {
    type = map(string)

    default = {
        dev = "input"
        prod = "input"
    }
}