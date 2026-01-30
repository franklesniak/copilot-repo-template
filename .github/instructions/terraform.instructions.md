---
applyTo: "**/*.tf,**/*.tfvars,**/*.tftest.hcl,**/*.tf.json,**/*.tftpl,**/*.tfbackend"
description: "Terraform coding standards: secure, modular, and well-documented infrastructure as code."
---

# Terraform Writing Style

**Version:** 1.2.20260130.0

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-01-30
- **Scope:** Defines Terraform coding standards for all `.tf`, `.tfvars`, `.tftest.hcl`, `.tf.json`, `.tftpl`, and `.tfbackend` files in this repository. Covers style, formatting, naming conventions, file organization, variable and output design, resource configuration, module design, refactoring, state management, security best practices, provider management, testing, and documentation requirements.
- **Related:** [Repository Copilot Instructions](../copilot-instructions.md)

## Table of Contents

- [Keywords](#keywords)
- [Quick Reference Checklist](#quick-reference-checklist)
- [Executive Summary: Terraform Philosophy](#executive-summary-terraform-philosophy)
- [Formatting and Style](#formatting-and-style)
- [Naming Conventions](#naming-conventions)
- [File Organization](#file-organization)
- [Variable and Output Design](#variable-and-output-design)
- [Resource Configuration](#resource-configuration)
- [Module Design](#module-design)
- [Refactoring](#refactoring)
- [State Management](#state-management)
- [Provider Management](#provider-management)
- [Security Best Practices](#security-best-practices)
- [Testing with Terraform Test](#testing-with-terraform-test)
- [Documentation Standards](#documentation-standards)
- [Pre-commit Discipline for Terraform](#pre-commit-discipline-for-terraform)
- ["Done" Definition for Terraform Changes](#done-definition-for-terraform-changes)
- [Scope Exceptions & Deviations from Standards](#scope-exceptions--deviations-from-standards)

## Keywords

The key words "**MUST**", "**MUST NOT**", "**REQUIRED**", "**SHALL**", "**SHALL NOT**", "**SHOULD**", "**SHOULD NOT**", "**RECOMMENDED**", "**MAY**", and "**OPTIONAL**" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

- **MUST** / **REQUIRED** / **SHALL** — Absolute requirement. Non-negotiable.
- **MUST NOT** / **SHALL NOT** — Absolute prohibition.
- **SHOULD** / **RECOMMENDED** — Strong recommendation. Valid reasons may exist to deviate, but implications must be understood.
- **SHOULD NOT** / **NOT RECOMMENDED** — Strong discouragement. Valid reasons may exist to do otherwise, but implications must be understood.
- **MAY** / **OPTIONAL** — Truly optional. Implementations can choose to include or omit.

## Quick Reference Checklist

This checklist provides a quick reference for both human developers and LLMs (like GitHub Copilot) to follow the Terraform style guidelines. Each item includes a scope tag indicating applicability:

- **[All]** — Applies to all Terraform files
- **[Module]** — Applies when developing reusable modules
- **[Root]** — Applies to root configurations (deployments)
- **[Test]** — Applies to test files (`.tftest.hcl`)

### Formatting and Style

- **[All]** Code **MUST** pass `terraform fmt` without modifications → [terraform fmt Compliance](#terraform-fmt-compliance)
- **[All]** Code **MUST** use 2 spaces for indentation, never tabs → [Indentation Rules](#indentation-rules)
- **[All]** Files **MUST** use UTF-8 encoding → [File Encoding](#file-encoding)
- **[All]** Files **MUST** end with a single newline → [File Endings](#file-endings)
- **[All]** Lines **SHOULD NOT** exceed 120 characters except for long strings or URLs → [Line Length](#line-length)
- **[All]** Blank lines **MUST** be completely empty (no whitespace) → [Blank Lines](#blank-lines)
- **[All]** Comments **MUST** use `#` for single-line; `/* */` **MAY** be used for multi-line → [Comment Style](#comment-style)

### Naming Conventions

- **[All]** Resources **MUST** use `snake_case` names → [Resource Naming](#resource-naming)
- **[All]** Variables **MUST** use `snake_case` with descriptive names → [Variable Naming](#variable-naming)
- **[All]** Outputs **MUST** use `snake_case` matching resource attribute patterns → [Output Naming](#output-naming)
- **[Module]** Module directory names **MUST** use hyphen-separated lowercase words → [Module Naming](#module-naming)
- **[All]** Data sources **MUST** be prefixed with purpose when multiple exist → [Data Source Naming](#data-source-naming)
- **[All]** Locals **MUST** use `snake_case` with descriptive names → [Local Value Naming](#local-value-naming)
- **[All]** Boolean variables **SHOULD** use `enable_*`, `is_*`, or `has_*` prefixes → [Boolean Naming Patterns](#boolean-naming-patterns)

### File Organization

- **[All]** Every Terraform directory **MUST** have a `versions.tf` file → [Version Constraints File](#version-constraints-file)
- **[All]** Input variables **MUST** be in `variables.tf` → [Standard File Organization](#standard-file-organization)
- **[All]** Outputs **MUST** be in `outputs.tf` → [Standard File Organization](#standard-file-organization)
- **[Root]** Root modules **MUST** have a `providers.tf` file → [Provider Configuration File](#provider-configuration-file)
- **[Root]** Root modules **MUST** have a `backend.tf` or backend configuration → [Backend Configuration](#backend-configuration)
- **[Module]** Modules **MUST** include a `README.md` → [Module README Requirements](#module-readme-requirements)
- **[Module]** Modules **SHOULD** include `examples/` directory → [Module Examples](#module-examples)
- **[Module]** Modules **SHOULD** include `tests/` directory → [Module Tests](#module-tests)

### Variable and Output Design

- **[All]** Variables **MUST** include a `description` → [Variable Documentation Requirements](#variable-documentation-requirements)
- **[All]** Variables **MUST** include explicit `type` constraint → [Variable Type Constraints](#variable-type-constraints)
- **[All]** Optional variables **MUST** have a `default` value → [Variable Defaults](#variable-defaults)
- **[All]** Sensitive variables **MUST** be marked with `sensitive = true` → [Sensitive Variable Marking](#sensitive-variable-marking)
- **[All]** Variables with constrained values **SHOULD** use `validation` blocks → [Variable Validation](#variable-validation)
- **[All]** Outputs **MUST** include a `description` → [Output Documentation Requirements](#output-documentation-requirements)
- **[All]** Sensitive outputs **MUST** be marked with `sensitive = true` → [Sensitive Output Marking](#sensitive-output-marking)

### Resource Configuration

- **[All]** Meta-arguments **MUST** appear first in resource blocks → [Meta-Argument Ordering](#meta-argument-ordering)
- **[All]** Required arguments **MUST** appear before optional arguments → [Argument Ordering](#argument-ordering)
- **[All]** Nested blocks **MUST** appear last in resource blocks → [Nested Block Placement](#nested-block-placement)
- **[All]** Resources **MUST** include required tags → [Required Tags](#required-tags)
- **[Root]** Provider-level default tags **SHOULD** be configured → [Default Tags Configuration](#default-tags-configuration)
- **[All]** Local values **SHOULD** be used for computed or merged tags → [Local Tags Pattern](#local-tags-pattern)

### Module Design

- **[Module]** Modules **MUST** have a single, well-defined responsibility → [Single Responsibility](#single-responsibility)
- **[Module]** Modules **MUST** specify required Terraform and provider versions → [Module Version Constraints](#module-version-constraints)
- **[Module]** Module inputs **MUST** use consistent naming across modules → [Module Interface Design](#module-interface-design)
- **[Module]** Required module variables **SHOULD** be minimized → [Minimal Required Inputs](#minimal-required-inputs)
- **[Module]** Complex inputs **SHOULD** use object types with documented structure → [Complex Input Types](#complex-input-types)
- **[Module]** Modules **SHOULD** expose only necessary outputs → [Module Output Design](#module-output-design)
- **[Module]** Published modules **MUST** use semantic versioning → [Module Versioning](#module-versioning)

### Refactoring

- **[All]** Resource renames **MUST** use `moved` blocks instead of manual state commands → [Refactoring with Moved Blocks](#refactoring-with-moved-blocks)
- **[All]** Existing infrastructure imports **SHOULD** use `import` blocks instead of CLI commands → [Importing Resources with Import Blocks](#importing-resources-with-import-blocks)
- **[All]** Resources removed from management **SHOULD** use `removed` blocks → [Removing Resources from State with Removed Blocks](#removing-resources-from-state-with-removed-blocks)
- **[All]** Direct state manipulation commands **SHOULD** be avoided → [State Manipulation Commands](#state-manipulation-commands)

### State Management

- **[Root]** Root modules **MUST** configure a remote backend → [Remote Backend Configuration](#remote-backend-configuration)
- **[Root]** State files **MUST** be encrypted at rest → [State Encryption](#state-encryption)
- **[Root]** State locking **MUST** be enabled → [State Locking](#state-locking)
- **[All]** Local state files **MUST NOT** be used in production → [No Local State in Production](#no-local-state-in-production)
- **[All]** State files **MUST NOT** be committed to version control → [State File Exclusion](#state-file-exclusion)

### Provider Management

- **[All]** Provider versions **MUST** be constrained → [Provider Version Constraints](#provider-version-constraints)
- **[All]** `.terraform.lock.hcl` **MUST** be committed to version control → [Lock File Management](#lock-file-management)
- **[All]** Pessimistic constraint operator (`~>`) **SHOULD** be used for providers → [Pessimistic Constraints](#pessimistic-constraints)

### Security

- **[All]** Secrets **MUST NOT** appear in `.tf` files → [Secret Management](#secret-management)
- **[All]** Secrets **MUST NOT** have default values → [No Secret Defaults](#no-secret-defaults)
- **[All]** Secrets **MUST** be provided via environment variables or secret managers → [Approved Secret Patterns](#approved-secret-patterns)
- **[Root]** State backends **MUST** enable encryption → [State Security](#state-security)
- **[All]** IAM policies **MUST** follow least-privilege principles → [Least-Privilege Principles](#least-privilege-principles)
- **[All]** Wildcard actions **SHOULD NOT** be used in IAM policies → [IAM Policy Guidelines](#iam-policy-guidelines)

### Testing

- **[Test]** Test files **MUST** use `.tftest.hcl` extension → [Test File Naming](#test-file-naming)
- **[Test]** Test files **SHOULD** be in a `tests/` directory → [Test File Location](#test-file-location)
- **[Test]** Tests **MUST** include at least one `run` block → [Test Structure](#test-structure)
- **[Test]** Each `run` block **MUST** include at least one `assert` → [Test Assertions](#test-assertions)
- **[Test]** Variable validation **SHOULD** be tested → [Testing Variable Validation](#testing-variable-validation)
- **[Test]** Unit tests **SHOULD** use `command = plan` → [Unit Tests](#unit-tests)
- **[Test]** Integration tests **MAY** use `command = apply` → [Integration Tests](#integration-tests)
- **[Module]** Modules **SHOULD** include corresponding Terraform tests → [Module Tests](#module-tests)
- **[Test]** Mock providers **SHOULD** be used for unit tests → [Mock Providers](#mock-providers)
- **[Test]** Negative test cases **SHOULD** use `expect_failures` → [Testing Variable Validation](#testing-variable-validation)

### Documentation

- **[Module]** Modules **MUST** have a `README.md` with usage examples → [Module README Requirements](#module-readme-requirements)
- **[All]** Inline comments **SHOULD** explain "why," not "what" → [Inline Comment Conventions](#inline-comment-conventions)
- **[All]** TODO comments **SHOULD** include username and context → [TODO Comment Format](#todo-comment-format)

### Code Authoring Guidelines

The following guidelines apply to all code authors, including human developers and AI assistants such as GitHub Copilot:

- **[All]** Authors **MUST NOT** invent providers, modules, or placeholder values without explicit confirmation of requirements
- **[All]** Authors **MUST** ask for or verify missing required information (e.g., `bucket`, `region`, `project_id`) rather than inserting assumptions
- **[All]** Authors **MUST NOT** include secrets, API keys, tokens, or hardcoded sensitive information in code
- **[All]** Authors **SHOULD** default to minimal, reproducible, and well-documented code
- **[All]** Authors **MUST** only modify backend configuration when explicitly required
- **[All]** Authors **SHOULD NOT** assume a default cloud provider; when the provider is not specified, authors **SHOULD** use provider-agnostic examples and document that provider selection is required
- **[All]** Authors **SHOULD** include `description` for all variables and outputs, and use `sensitive = true` as appropriate
- **[All]** Authors **MUST NOT** modify lock files (`.terraform.lock.hcl`) or commit state unless explicitly required
- **[All]** Authors **MUST** use placeholder markers following the `REPLACE_ME_*` pattern (e.g., `REPLACE_ME_BUCKET`, `REPLACE_ME_REGION`) for values that require customization

## Executive Summary: Terraform Philosophy

This repository approaches Terraform as **infrastructure as code** with the same rigor applied to application code. The following principles guide all Terraform development:

- **Deterministic and reproducible:** Infrastructure changes **MUST** produce predictable, repeatable results. The same configuration **MUST** produce the same infrastructure across environments.

- **Security-first:** Secrets **MUST NEVER** appear in code or state unencrypted. Least-privilege **MUST** be the default for all IAM policies and resource access controls.

- **Modular and reusable:** Common infrastructure patterns **SHOULD** be extracted into versioned modules with well-defined interfaces. Modules **MUST** be designed for reuse across projects.

- **Well-documented:** Every variable, output, and module **MUST** be documented. Documentation is not optional—it is a first-class deliverable.

- **Testable:** Infrastructure **SHOULD** be validated with automated tests before deployment. Terraform's native test framework enables validation of configuration logic.

- **Version-controlled:** All Terraform code, including lock files, **MUST** be version-controlled. State files **MUST** be stored remotely with encryption and locking.

The coding standards in this document enforce these principles through specific, actionable requirements.

> **Provider-Agnostic Guidance:** Throughout this document, AWS is used for illustration in code examples, but all style rules and best practices are **provider-agnostic**. Users **MAY** substitute Azure (`azurerm`), Google Cloud (`google`), or any other Terraform provider to suit their use case. The principles of naming, structure, security, and documentation apply equally across all providers.

---

## Formatting and Style

### terraform fmt Compliance

All Terraform code **MUST** pass `terraform fmt` without modifications. This is non-negotiable.

**Verification command:**

```bash
terraform fmt -check -recursive
```

**Auto-format command:**

```bash
terraform fmt -recursive
```

**Pre-commit integration:**

```yaml
- repo: https://github.com/antonbabenko/pre-commit-terraform
  rev: v1.96.3
  hooks:
    - id: terraform_fmt
```

### Indentation Rules

- Code **MUST** use 2 spaces for indentation
- Tabs **MUST NOT** be used
- Nested blocks **MUST** maintain consistent indentation
- Alignment of `=` signs is handled automatically by `terraform fmt`

**Compliant:**

```hcl
resource "aws_instance" "example" {
  ami           = var.ami_id
  instance_type = var.instance_type

  tags = {
    Name        = var.instance_name
    Environment = var.environment
  }
}
```

### File Encoding

All Terraform files **MUST** use UTF-8 encoding without BOM (Byte Order Mark).

### File Endings

All files **MUST** end with a single newline character. Trailing blank lines **MUST NOT** be present.

### Line Length

Lines **SHOULD NOT** exceed 120 characters. Exceptions are permitted for:

- Long strings that cannot be reasonably split
- URLs in comments or string values
- Complex expressions where splitting reduces readability

### Blank Lines

Blank lines **MUST** be completely empty—they **MUST NOT** contain any whitespace characters (spaces or tabs).

Use blank lines to:

- Separate logical sections within a file
- Separate resource blocks
- Separate groups of related arguments within a block

### Comment Style

**Single-line comments:**

Use `#` for single-line comments. Comments **SHOULD** be placed on their own line above the code they describe.

```hcl
# Enable encryption to meet compliance requirements
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  # ...
}
```

**Multi-line comments:**

Use `/* */` sparingly for multi-line explanations when a single `#` comment is insufficient.

```hcl
/*
 * This security group allows inbound traffic from the corporate VPN.
 * CIDR ranges are managed by the network team and should not be
 * modified without their approval.
 */
resource "aws_security_group" "vpn_access" {
  # ...
}
```

---

## Naming Conventions

### Resource Naming

Resources **MUST** use `snake_case` for names. Names **SHOULD** be descriptive and indicate purpose.

| Resource Type | Naming Pattern | Example |
| --- | --- | --- |
| Primary/main resource | `main` or descriptive name | `aws_instance.main` |
| Multiple of same type | Purpose-based suffix | `aws_instance.web_server` |
| Associated resources | Parent reference | `aws_security_group.web_server` |

**Anti-patterns to avoid:**

| Bad | Good | Reason |
| --- | --- | --- |
| `aws_instance.this` | `aws_instance.main` | "this" is not descriptive |
| `aws_instance.instance1` | `aws_instance.primary` | Numeric suffixes are meaningless |
| `aws_instance.MyInstance` | `aws_instance.my_instance` | Must be snake_case |
| `aws_instance.i` | `aws_instance.web_server` | Single-letter names lack meaning |

### Variable Naming

Variables **MUST** use `snake_case` and **MUST** be descriptive.

| Category | Pattern | Example |
| --- | --- | --- |
| Simple values | `<noun>` or `<adjective>_<noun>` | `instance_type`, `environment` |
| Lists/Sets | Plural nouns | `subnet_ids`, `security_group_ids` |
| Maps | `<noun>_map` or descriptive | `tags`, `instance_settings` |
| Booleans | `enable_*`, `is_*`, `has_*` | `enable_monitoring`, `is_public` |
| Resource references | `<resource>_id` or `<resource>_arn` | `vpc_id`, `role_arn` |

**Compliant variable names:**

```hcl
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "enable_monitoring" {
  description = "Enable CloudWatch detailed monitoring"
  type        = bool
  default     = false
}

variable "subnet_ids" {
  description = "List of subnet IDs for deployment"
  type        = list(string)
}
```

### Output Naming

Outputs **MUST** use `snake_case` and **SHOULD** follow the pattern of the attribute being exposed.

| Output Type | Pattern | Example |
| --- | --- | --- |
| Resource ID | `<resource>_id` | `instance_id`, `vpc_id` |
| Resource ARN | `<resource>_arn` | `role_arn`, `bucket_arn` |
| Resource name | `<resource>_name` | `bucket_name`, `cluster_name` |
| Endpoints/URLs | `<resource>_endpoint` | `rds_endpoint`, `api_endpoint` |
| Collections | Plural form | `instance_ids`, `subnet_ids` |

### Module Naming

Module directory names **MUST** use hyphen-separated lowercase words.

**Compliant:**

```text
modules/
├── vpc-network/
├── ec2-instance/
├── rds-database/
└── s3-bucket/
```

**Non-compliant:**

```text
modules/
├── VpcNetwork/        # PascalCase
├── ec2_instance/      # snake_case
└── rdsdatabase/       # No separation
```

### Data Source Naming

When multiple data sources of the same type exist, they **MUST** be prefixed with their purpose.

**Single data source:**

```hcl
data "aws_ami" "amazon_linux" {
  # ...
}
```

**Multiple data sources:**

```hcl
data "aws_ami" "web_server" {
  # ...
}

data "aws_ami" "database_server" {
  # ...
}
```

### Local Value Naming

Local values **MUST** use `snake_case` with descriptive names.

```hcl
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }

  instance_name = "${var.project_name}-${var.environment}"
}
```

### Boolean Naming Patterns

Boolean variables and locals **SHOULD** use these prefixes:

| Prefix | Use Case | Example |
| --- | --- | --- |
| `enable_*` | Feature flags | `enable_monitoring`, `enable_encryption` |
| `is_*` | State checks | `is_public`, `is_production` |
| `has_*` | Presence checks | `has_custom_domain`, `has_ssl_certificate` |

---

## File Organization

### Standard File Organization

Standard file organization for Terraform projects:

| File | Purpose | Required |
| --- | --- | --- |
| `main.tf` | Primary resource definitions | Yes |
| `variables.tf` | Input variable declarations | Yes |
| `outputs.tf` | Output value declarations | Yes |
| `providers.tf` | Provider configuration | Yes (root modules) |
| `versions.tf` | Version constraints | Yes |
| `locals.tf` | Local value definitions | When needed |
| `data.tf` | Data source definitions | When needed |
| `backend.tf` | Backend configuration | Root modules only |

### Version Constraints File

Every Terraform directory **MUST** have a `versions.tf` file with Terraform and provider version constraints:

```hcl
# versions.tf

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

### Provider Configuration File

Root modules **MUST** have a `providers.tf` file with provider configuration:

```hcl
# providers.tf

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    }
  }
}
```

### Backend Configuration

Root modules **MUST** configure a remote backend, either in `backend.tf` or within the `terraform` block:

```hcl
# backend.tf

terraform {
  backend "s3" {
    bucket         = "REPLACE_ME_STATE_BUCKET"
    key            = "environments/prod/terraform.tfstate"
    region         = "REPLACE_ME_REGION"
    encrypt        = true
    dynamodb_table = "REPLACE_ME_LOCK_TABLE"
  }
}
```

#### Partial Backend Configuration

As an alternative to placeholder values, Terraform supports **partial backend configuration**. This pattern separates static configuration (committed to version control) from dynamic values (provided at runtime):

**Backend file (committed):**

```hcl
# backend.tf - partial configuration

terraform {
  backend "s3" {
    key     = "environments/prod/terraform.tfstate"
    encrypt = true
    # bucket, region, and dynamodb_table provided via -backend-config
  }
}
```

**Backend config file (environment-specific):**

```hcl
# config/prod.s3.tfbackend

bucket         = "my-org-terraform-state"
region         = "us-east-1"
dynamodb_table = "terraform-locks"
```

**Usage:**

```bash
terraform init -backend-config=config/prod.s3.tfbackend
```

This pattern is useful when:

- Backend values vary by environment but the state key structure is consistent
- Teams prefer runtime configuration over placeholder replacement
- CI/CD pipelines inject backend configuration dynamically

Both the `REPLACE_ME_*` placeholder pattern and partial configuration pattern are valid approaches. Choose the pattern that best fits your team's workflow.

### Variable Files (.tfvars)

Terraform variable files (`.tfvars`) provide environment-specific or deployment-specific values. This section defines conventions for organizing and managing these files.

#### Naming Conventions

| Pattern | Use Case | Example |
| --- | --- | --- |
| `terraform.tfvars` | Default values loaded automatically | `terraform.tfvars` |
| `<environment>.tfvars` | Environment-specific values | `prod.tfvars`, `dev.tfvars` |
| `<environment>.auto.tfvars` | Auto-loaded environment values | `prod.auto.tfvars` |

#### Content Guidelines

**What belongs in `.tfvars` files:**

- Environment-specific values (e.g., instance sizes, replica counts)
- Non-sensitive configuration overrides
- Deployment-specific settings

**What does NOT belong in `.tfvars` files:**

- Secrets, API keys, or passwords — see [Security Best Practices](#security-best-practices)
- Hardcoded credentials or tokens
- Any value that should not be committed to version control

**Relationship to variable defaults:**

Values in `.tfvars` files override `default` values in variable declarations. The loading order is:

1. `default` value in `variables.tf`
2. Environment variables (`TF_VAR_name`)
3. `terraform.tfvars` and `terraform.tfvars.json` (if present)
4. `*.auto.tfvars` and `*.auto.tfvars.json` files (in alphabetical order)
5. `-var-file` command-line arguments (in order specified)
6. `-var` command-line arguments (later flags override earlier ones)

#### Version Control Guidelines

- Non-sensitive `.tfvars` files **MAY** be committed to version control
- Sensitive `.tfvars` files **MUST NOT** be committed; use `.tfvars.example` templates instead
- Template files **SHOULD** use the `.tfvars.example` extension to indicate they require customization

**Example `.gitignore` patterns for sensitive tfvars:**

```gitignore
# Sensitive variable files (use *.tfvars.example as templates)
*.sensitive.tfvars
*-secrets.tfvars
```

#### Example File Structure

```text
environments/
├── prod/
│   ├── main.tf
│   ├── variables.tf
│   ├── terraform.tfvars        # Committed: non-sensitive defaults
│   ├── secrets.tfvars.example  # Committed: template for secrets
│   └── secrets.tfvars          # NOT committed: actual secrets
└── dev/
    ├── main.tf
    ├── variables.tf
    └── terraform.tfvars
```

### Module Directory Structure

Standard module directory structure:

```text
modules/
└── <module-name>/
    ├── main.tf           # Primary resources
    ├── variables.tf      # Input variables (REQUIRED)
    ├── outputs.tf        # Output values (REQUIRED)
    ├── versions.tf       # Version constraints (REQUIRED)
    ├── README.md         # Module documentation (REQUIRED)
    ├── locals.tf         # Local values (when needed)
    ├── data.tf           # Data sources (when needed)
    ├── examples/         # Usage examples (RECOMMENDED)
    │   └── basic/
    │       ├── main.tf
    │       ├── variables.tf
    │       └── outputs.tf
    └── tests/            # Test files (RECOMMENDED)
        └── basic.tftest.hcl
```

### Module Examples

Modules **SHOULD** include an `examples/` directory with working examples:

- Each example **MUST** be a complete, runnable configuration
- Examples **SHOULD** demonstrate common use cases
- Examples **SHOULD** include a `README.md` explaining the example

### Module Tests

Modules **SHOULD** include a `tests/` directory with Terraform test files:

- Tests **MUST** use the `.tftest.hcl` extension
- Tests **SHOULD** cover both valid and invalid inputs
- Tests **SHOULD** validate critical outputs

---

## Variable and Output Design

### Variable Documentation Requirements

Every variable **MUST** include a `description`. The description **SHOULD** explain:

- What the variable is for
- Valid values or constraints
- Any special considerations

```hcl
variable "environment" {
  description = "Deployment environment. Valid values: dev, staging, prod."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
```

### Variable Type Constraints

Variables **MUST** include explicit `type` constraints:

```hcl
# String variable
variable "instance_type" {
  description = "EC2 instance type for the application server."
  type        = string
  default     = "t3.micro"
}

# List variable
variable "subnet_ids" {
  description = "List of subnet IDs for deployment."
  type        = list(string)
}

# Map variable
variable "tags" {
  description = "Additional tags to apply to resources."
  type        = map(string)
  default     = {}
}

# Object variable
variable "instance_config" {
  description = "Configuration for the EC2 instance."
  type = object({
    instance_type = string
    ami_id        = string
    volume_size   = optional(number, 20)
  })
}
```

### Variable Defaults

Optional variables **MUST** have a `default` value. Required variables **MUST NOT** have a `default`.

```hcl
# Required variable (no default)
variable "vpc_id" {
  description = "VPC ID where resources will be created."
  type        = string
}

# Optional variable (has default)
variable "enable_monitoring" {
  description = "Enable CloudWatch detailed monitoring."
  type        = bool
  default     = false
}
```

### Variable Validation

Variables with constrained values **SHOULD** use `validation` blocks:

```hcl
variable "environment" {
  description = "Deployment environment. Valid values: dev, staging, prod."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "instance_count" {
  description = "Number of instances to create. Must be between 1 and 10."
  type        = number

  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

variable "cidr_block" {
  description = "CIDR block for the VPC."
  type        = string

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be a valid CIDR block."
  }
}
```

### Sensitive Variable Marking

Variables containing sensitive data **MUST** be marked:

```hcl
variable "database_password" {
  description = "Password for the RDS database. Must be provided via environment variable or tfvars."
  type        = string
  sensitive   = true
}

variable "api_key" {
  description = "API key for external service"
  type        = string
  sensitive   = true
}
```

### Output Documentation Requirements

Every output **MUST** include a `description`:

```hcl
output "instance_id" {
  description = "The ID of the created EC2 instance."
  value       = aws_instance.main.id
}

output "instance_public_ip" {
  description = "The public IP address of the EC2 instance."
  value       = aws_instance.main.public_ip
}
```

### Sensitive Output Marking

Outputs containing sensitive data **MUST** be marked:

```hcl
output "database_connection_string" {
  description = "Database connection string (contains credentials)."
  value       = local.connection_string
  sensitive   = true
}

output "instance_private_ip" {
  description = "The private IP address of the EC2 instance."
  value       = aws_instance.main.private_ip
  sensitive   = true
}
```

---

## Resource Configuration

### Meta-Argument Ordering

Within resource blocks, arguments **MUST** follow this order:

1. **Meta-arguments first:** `count`, `for_each`, `provider`, `depends_on`, `lifecycle`
2. **Required arguments:** Arguments without defaults
3. **Optional arguments:** Arguments with defaults
4. **Nested blocks last:** Dynamic blocks, inline blocks

**Compliant example:**

```hcl
resource "aws_instance" "web_server" {
  # Meta-arguments first
  count    = var.instance_count
  provider = aws.primary

  # Required arguments
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id

  # Optional arguments
  associate_public_ip_address = var.is_public
  monitoring                  = var.enable_monitoring

  # Nested blocks last
  root_block_device {
    volume_size = var.root_volume_size
    encrypted   = true
  }

  tags = local.common_tags

  # Lifecycle block at the end
  lifecycle {
    create_before_destroy = true
  }
}
```

### Argument Ordering

Within the arguments section:

1. Required arguments appear before optional arguments
2. Related arguments are grouped together
3. `tags` typically appears last before nested blocks

### Nested Block Placement

Nested blocks **MUST** appear after all simple arguments:

```hcl
resource "aws_security_group" "web" {
  # Simple arguments first
  name        = "${var.project_name}-web-sg"
  description = "Security group for web servers"
  vpc_id      = var.vpc_id

  # Nested blocks last
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}
```

### Required Tags

All taggable resources **MUST** include these tags:

| Tag | Description | Example |
| --- | --- | --- |
| `Name` | Human-readable resource name | `prod-web-server-1` |
| `Environment` | Deployment environment | `prod`, `staging`, `dev` |
| `Project` | Project or application name | `my-application` |
| `ManagedBy` | Management method | `terraform` |
| `Owner` | Team or individual owner | `platform-team` |

### Default Tags Configuration

Root modules **SHOULD** use provider-level default tags to ensure consistent tagging:

```hcl
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
      Owner       = var.owner_team
    }
  }
}
```

### Local Tags Pattern

Use locals for computed or merged tags:

```hcl
locals {
  common_tags = {
    Name        = "${var.project_name}-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }

  # Merge common tags with resource-specific tags
  instance_tags = merge(local.common_tags, {
    Role = "web-server"
  })
}
```

---

## Module Design

### Single Responsibility

Modules **MUST** have a single, well-defined responsibility:

- Each module **SHOULD** manage one logical component
- Modules **SHOULD NOT** try to do too much
- Complex infrastructure **SHOULD** be composed of multiple modules

**Good:** A VPC module that creates VPC, subnets, route tables, and internet gateway.

**Bad:** A "full-stack" module that creates VPC, EC2, RDS, and S3 all together.

### Module Version Constraints

Modules **MUST** specify required Terraform and provider versions:

```hcl
# versions.tf in module directory

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0.0"
    }
  }
}
```

### Module Interface Design

**Inputs:**

- Variable names **MUST** be consistent across modules (e.g., always `environment`, not sometimes `env`)
- Required variables **SHOULD** be minimized to essential values
- Complex inputs **SHOULD** use object types with documented structure

**Outputs:**

- Expose only values needed by calling modules
- Use consistent naming patterns across modules
- Document output types and formats

### Minimal Required Inputs

Required variables **SHOULD** be minimized. Provide sensible defaults where possible:

```hcl
# Good: Only truly required inputs are mandatory
variable "vpc_id" {
  description = "VPC ID where resources will be created."
  type        = string
  # No default - this is genuinely required
}

variable "instance_type" {
  description = "EC2 instance type."
  type        = string
  default     = "t3.micro"  # Sensible default
}
```

### Complex Input Types

For complex inputs, use object types with clear documentation:

```hcl
variable "instance_config" {
  description = <<-EOT
    Configuration for the EC2 instance.

    Attributes:
      - instance_type: EC2 instance type (e.g., "t3.micro")
      - ami_id: AMI ID to use for the instance
      - volume_size: Root volume size in GB (default: 20)
      - enable_monitoring: Enable detailed monitoring (default: false)
  EOT
  type = object({
    instance_type     = string
    ami_id            = string
    volume_size       = optional(number, 20)
    enable_monitoring = optional(bool, false)
  })
}
```

### Module Output Design

Outputs **SHOULD** expose only values needed by calling modules:

```hcl
# Good: Specific, useful outputs
output "instance_id" {
  description = "The ID of the created EC2 instance."
  value       = aws_instance.main.id
}

output "instance_private_ip" {
  description = "The private IP address of the EC2 instance."
  value       = aws_instance.main.private_ip
}

# Avoid: Exposing entire resource
output "instance" {
  description = "The entire instance resource."
  value       = aws_instance.main  # Too broad
}
```

### Module Versioning

For published modules, use semantic versioning:

- **MAJOR:** Breaking changes (removed inputs, changed behavior)
- **MINOR:** New features, backward-compatible changes
- **PATCH:** Bug fixes, documentation updates

Pin module versions in root configurations:

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  # ...
}

module "internal_module" {
  source = "./modules/my-module"
  # Local modules don't use version constraint
}
```

---

## Refactoring

Terraform provides declarative blocks for safely refactoring infrastructure without manual state manipulation. These blocks enable auditable, version-controlled changes that can be reviewed and tested before applying.

### Refactoring with Moved Blocks

The `moved` block (Terraform 1.1+) enables renaming or restructuring resources without destroying and recreating them. This is essential for:

- Renaming resources to follow updated naming conventions
- Restructuring modules
- Moving resources between modules

**Syntax and Example:**

```hcl
moved {
  from = aws_instance.web
  to   = aws_instance.web_server
}

resource "aws_instance" "web_server" {
  # Previously aws_instance.web
  ami           = var.ami_id
  instance_type = var.instance_type
  # ...
}
```

**Requirements:**

- You **MUST** run `terraform plan` before applying the `moved` block changes and again after applying/refactoring to verify that no unexpected changes remain
- The `moved` block **SHOULD** remain in configuration until all environments have been updated
- After all state has been migrated, `moved` blocks **MAY** be removed

### Importing Resources with Import Blocks

The `import` block (Terraform 1.5+) brings existing infrastructure under Terraform management. This is preferred over the `terraform import` CLI command because:

- Import configuration is version-controlled and reviewable
- Multiple imports can be planned and applied together
- Import intentions are visible in code review

**Syntax and Example:**

```hcl
import {
  to = aws_instance.example
  id = "REPLACE_ME_INSTANCE_ID"
}

resource "aws_instance" "example" {
  # Configuration matching the imported resource
  ami           = "REPLACE_ME_AMI_ID"
  instance_type = "REPLACE_ME_INSTANCE_TYPE"
  # ...
}
```

**Requirements:**

- The resource configuration **MUST** match the existing infrastructure
- You **MUST** run `terraform plan` before applying imports to verify the import will not cause unintended changes
- After successful import and apply, you **SHOULD** run `terraform plan` again to verify no further changes are pending, and `import` blocks **SHOULD** then be removed from configuration

### Removing Resources from State with Removed Blocks

The `removed` block (Terraform 1.7+) removes resources from Terraform management without destroying the underlying infrastructure. Use cases include:

- Transitioning resource ownership to another team or configuration
- Removing resources that are now managed outside Terraform
- Cleaning up state without affecting production infrastructure

**Syntax and Example:**

```hcl
removed {
  from = aws_instance.legacy

  lifecycle {
    destroy = false  # Remove from state without destroying
  }
}
```

**The `lifecycle.destroy` Option:**

| Value | Behavior |
| --- | --- |
| `true` (default) | Resource is destroyed when removed from configuration |
| `false` | Resource is removed from state but preserved in the cloud |

**Requirements:**

- Use `destroy = false` when the resource **MUST** continue to exist
- The reason for removal **MUST** be documented in comments or commit messages
- After successful apply, `removed` blocks **MAY** be removed from configuration

### State Manipulation Commands

Direct state manipulation commands (`terraform state mv`, `terraform state rm`, `terraform import`) **SHOULD** be avoided in favor of the declarative blocks above. The declarative approach provides:

- Version control and audit trail
- Code review before changes
- Consistent behavior across team members
- Reduced risk of human error

**When state commands are necessary, they MUST be:**

- Documented in commit messages with clear rationale
- Performed only after creating state backups
- Reviewed by a second team member when possible
- Followed by verification that state is consistent

**Backup command before state manipulation:**

```bash
terraform state pull > terraform.tfstate.backup
```

---

## State Management

> **Note:** For state modification best practices including resource renaming, importing existing infrastructure, and removing resources from management, see the [Refactoring](#refactoring) section.

### Remote Backend Configuration

Root modules **MUST** configure a remote backend for team environments:

```hcl
terraform {
  backend "s3" {
    bucket         = "REPLACE_ME_STATE_BUCKET"
    key            = "environments/prod/terraform.tfstate"
    region         = "REPLACE_ME_REGION"
    encrypt        = true
    dynamodb_table = "REPLACE_ME_LOCK_TABLE"
  }
}
```

> **Placeholder Values:** The example above uses placeholder values (e.g., `REPLACE_ME_STATE_BUCKET`). Replace these with your organization's actual values when adopting this template.

**Backend requirements:**

- State files **MUST** be encrypted at rest
- State access **MUST** be controlled via appropriate access controls (e.g., IAM for AWS, RBAC for Azure, IAM for GCP)
- State locking **MUST** be enabled to prevent concurrent modifications
- State files **MUST NOT** be committed to version control

### Terraform Cloud, Enterprise, and Alternative Backends

Organizations using **Terraform Cloud**, **Terraform Enterprise**, **Spacelift**, or similar workflow tools **MAY** use alternative state management approaches. In these cases:

- The `backend.tf` file **MAY** be omitted if state is managed by the orchestration platform.
- The `cloud` block **MAY** replace the `backend` block for Terraform Cloud/Enterprise integrations.
- Document your backend approach in the [Scope Exceptions](#scope-exceptions--deviations-from-standards) section.

**Example Terraform Cloud configuration:**

```hcl
terraform {
  cloud {
    organization = "REPLACE_ME_ORG"
    workspaces {
      name = "REPLACE_ME_WORKSPACE"
    }
  }
}
```

When using alternative backends, the following sections still apply:

- State encryption requirements (handled by the platform)
- State locking requirements (typically automatic with cloud backends)
- Version control exclusion of state files

The following sections **MAY** not apply when using Terraform Cloud/Enterprise:

- Manual `backend.tf` configuration
- DynamoDB lock table configuration
- S3/GCS/Azure Storage bucket configuration

### State Encryption

State backends **MUST** enable encryption:

```hcl
# S3 backend with encryption (example - replace values)
terraform {
  backend "s3" {
    bucket  = "REPLACE_ME_STATE_BUCKET"
    key     = "prod/terraform.tfstate"
    region  = "REPLACE_ME_REGION"
    encrypt = true  # REQUIRED
  }
}
```

### State Locking

State backends **MUST** support and enable state locking:

```hcl
# S3 backend with DynamoDB locking (example - replace values)
terraform {
  backend "s3" {
    bucket         = "REPLACE_ME_STATE_BUCKET"
    key            = "prod/terraform.tfstate"
    region         = "REPLACE_ME_REGION"
    encrypt        = true
    dynamodb_table = "REPLACE_ME_LOCK_TABLE"  # REQUIRED for locking
  }
}
```

### No Local State in Production

Local state files **MUST NOT** be used for production environments. Local state:

- Cannot be shared across team members
- Has no locking mechanism
- Has no encryption at rest
- Is easily lost or corrupted

### State File Exclusion

State files and related artifacts **MUST NOT** be committed to version control. Add to `.gitignore`:

```gitignore
# Terraform state files
*.tfstate
*.tfstate.*

# Crash log files
crash.log
crash.*.log

# .terraform directories
**/.terraform/*

# Override files
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# CLI configuration
.terraformrc
terraform.rc
```

### State File Organization

Organize state files by environment and component:

```text
state-bucket/
├── environments/
│   ├── dev/
│   │   └── terraform.tfstate
│   ├── staging/
│   │   └── terraform.tfstate
│   └── prod/
│       └── terraform.tfstate
└── shared/
    ├── networking/
    │   └── terraform.tfstate
    └── iam/
        └── terraform.tfstate
```

### Workspace Usage

Workspaces **MAY** be used for environment separation in simple cases:

```bash
terraform workspace select prod
terraform apply
```

**Caution:** For complex environments, separate state files per environment are often clearer than workspaces.

---

## Provider Management

### Provider Version Constraints

Provider versions **MUST** be constrained in `versions.tf`:

| Pattern | Example | Use Case |
| --- | --- | --- |
| Pessimistic constraint | `~> 5.0` | Allow minor version updates only |
| Exact version | `= 5.31.0` | Strict reproducibility required |
| Range constraint | `>= 5.0, < 6.0` | Explicit major version bounds |

**Recommended approach:**

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}
```

### Lock File Management

The `.terraform.lock.hcl` file:

- **MUST** be committed to version control
- **SHOULD** be updated explicitly using `terraform providers lock`
- **MUST** be updated when provider versions change
- **SHOULD** include hashes for all platforms used in CI

```bash
# Update lock file with hashes for multiple platforms
terraform providers lock \
  -platform=linux_amd64 \
  -platform=linux_arm64 \
  -platform=darwin_amd64 \
  -platform=darwin_arm64 \
  -platform=windows_amd64 \
  -platform=windows_arm64
```

### Pessimistic Constraints

Use the pessimistic constraint operator (`~>`) for providers to allow patch updates while preventing breaking changes:

```hcl
# Good: Allows 5.x updates but not 6.0
version = "~> 5.0"

# Good: Allows 5.31.x updates but not 5.32.0
version = "~> 5.31.0"
```

---

## Security Best Practices

### Secret Management

Secrets **MUST NEVER** appear in Terraform code or version control.

#### Prohibited Patterns

The following patterns are **PROHIBITED**:

```hcl
# NEVER DO THIS
variable "db_password" {
  default = "SuperSecretPassword123!"  # PROHIBITED
}

resource "aws_db_instance" "main" {
  password = "hardcoded-password"  # PROHIBITED
}
```

### No Secret Defaults

Sensitive variables **MUST NOT** have default values:

```hcl
# Correct: No default for secrets
variable "database_password" {
  description = "Database password. Set via TF_VAR_database_password."
  type        = string
  sensitive   = true
  # No default!
}
```

### Approved Secret Patterns

**Pattern 1: Environment Variables**

```hcl
variable "db_password" {
  description = "Database password. Set via TF_VAR_db_password environment variable."
  type        = string
  sensitive   = true
}
```

```bash
export TF_VAR_db_password="$(aws secretsmanager get-secret-value --secret-id my-secret --query SecretString --output text)"
terraform apply
```

**Pattern 2: AWS Secrets Manager**

```hcl
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "prod/database/password"
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}
```

**Pattern 3: HashiCorp Vault**

```hcl
data "vault_generic_secret" "db_creds" {
  path = "secret/data/database"
}

resource "aws_db_instance" "main" {
  username = data.vault_generic_secret.db_creds.data["username"]
  password = data.vault_generic_secret.db_creds.data["password"]
}
```

### Sensitive Variable Marking

Variables containing sensitive data **MUST** be marked:

```hcl
variable "api_key" {
  description = "API key for external service"
  type        = string
  sensitive   = true  # REQUIRED for secrets
}

output "connection_string" {
  description = "Database connection string (contains credentials)"
  value       = local.connection_string
  sensitive   = true  # REQUIRED if contains secrets
}
```

### State Security

State files contain sensitive data and **MUST** be protected.

#### Requirements

1. **Encryption at rest:** State backends **MUST** enable encryption
2. **Access control:** State files **MUST** be accessible only to authorized users/roles
3. **No local state in production:** Local state files **MUST NOT** be used for production
4. **State locking:** Backends **MUST** support state locking

#### S3 Backend Security Configuration

```hcl
terraform {
  backend "s3" {
    bucket         = "REPLACE_ME_STATE_BUCKET"
    key            = "prod/terraform.tfstate"
    region         = "REPLACE_ME_REGION"
    encrypt        = true                    # REQUIRED
    dynamodb_table = "REPLACE_ME_LOCK_TABLE"  # REQUIRED for locking
    # Use IAM role or credentials from environment
  }
}
```

### Least-Privilege Principles

IAM policies and resource permissions **MUST** follow least-privilege:

#### IAM Policy Guidelines

- Grant only required permissions
- Use resource-level restrictions when possible
- Avoid wildcard actions (`*`) except when truly needed
- Use conditions to further restrict access

```hcl
# GOOD: Specific permissions
resource "aws_iam_policy" "s3_reader" {
  name = "s3-reader"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data.arn,
          "${aws_s3_bucket.data.arn}/*"
        ]
      }
    ]
  })
}

# BAD: Overly permissive
resource "aws_iam_policy" "bad_example" {
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:*"]       # TOO BROAD
      Resource = ["*"]           # TOO BROAD
    }]
  })
}
```

### Security Scanning

Security scanning tools **SHOULD** be integrated into the development workflow.

#### Recommended Tools

| Tool | Purpose | Integration |
| --- | --- | --- |
| `tfsec` | Static security analysis | Pre-commit, CI |
| `checkov` | Policy-as-code scanning | Pre-commit, CI |
| `terrascan` | Security and compliance | CI |
| `trivy` | Misconfiguration scanning | CI |

#### Pre-commit Integration Example

```yaml
- repo: https://github.com/antonbabenko/pre-commit-terraform
  rev: v1.96.3
  hooks:
    - id: terraform_tfsec
    - id: terraform_checkov
```

---

## Testing with Terraform Test

Terraform's native test framework (introduced in Terraform 1.6) provides a way to validate configurations without external testing tools. This section documents testing conventions that integrate with the coding standards in this guide.

> **Note:** Terraform tests require Terraform 1.6.0 or later. For older Terraform versions, consider Terratest or other external testing frameworks.

### Test File Naming

Test files **MUST** use the `.tftest.hcl` extension:

- `basic.tftest.hcl`
- `validation.tftest.hcl`
- `integration.tftest.hcl`

### Test File Location

Test files **SHOULD** be placed in a `tests/` directory within the module:

```text
modules/
└── vpc/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── versions.tf
    ├── README.md
    └── tests/
        ├── basic.tftest.hcl
        ├── validation.tftest.hcl
        └── integration.tftest.hcl
```

**Alternative:** Tests alongside configuration:

```text
modules/
└── vpc/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── vpc.tftest.hcl
    └── vpc_validation.tftest.hcl
```

### Test Structure

Terraform test files use HCL syntax with specific blocks.

#### Basic Test Structure

```hcl
# tests/basic.tftest.hcl

# Variables block (optional) - Set values for tests
variables {
  environment = "test"
  vpc_cidr    = "10.0.0.0/16"
}

# Run block - Defines a test scenario
run "creates_vpc_with_correct_cidr" {
  command = plan  # or apply

  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "VPC CIDR block does not match expected value"
  }
}

run "creates_required_subnets" {
  command = plan

  assert {
    condition     = length(aws_subnet.private) == 3
    error_message = "Expected 3 private subnets"
  }
}
```

#### Test Block Reference

| Block | Purpose | Required |
| --- | --- | --- |
| `variables {}` | Set input variable values for tests | Optional |
| `provider {}` | Configure provider for tests (e.g., mock) | Optional |
| `run "name" {}` | Define a test scenario | Required (at least one) |
| `assert {}` | Define a test assertion within a run | Required (at least one per run) |
| `expect_failures` | Expect specific resources/outputs to fail | Optional |

### Test Assertions

Each `run` block **MUST** include at least one `assert`:

```hcl
run "instance_has_correct_type" {
  command = plan

  assert {
    condition     = aws_instance.main.instance_type == var.instance_type
    error_message = "Instance type mismatch"
  }

  assert {
    condition     = aws_instance.main.tags["Environment"] == "test"
    error_message = "Instance must have Environment tag"
  }
}
```

### Testing Variable Validation

Test validation rules with `expect_failures`:

```hcl
run "rejects_invalid_environment" {
  command = plan

  variables {
    environment = "invalid"  # Should fail validation
  }

  expect_failures = [
    var.environment
  ]
}

run "accepts_valid_environment" {
  command = plan

  variables {
    environment = "prod"
  }

  assert {
    condition     = var.environment == "prod"
    error_message = "Environment should be prod"
  }
}
```

### Testing Outputs

```hcl
run "outputs_vpc_id" {
  command = apply

  assert {
    condition     = output.vpc_id != null && output.vpc_id != ""
    error_message = "vpc_id output must not be empty"
  }
}

run "outputs_correct_subnet_count" {
  command = apply

  assert {
    condition     = length(output.subnet_ids) == 3
    error_message = "Expected 3 subnet IDs in output"
  }
}
```

### Mock Providers

For unit testing without real infrastructure, use mock providers:

```hcl
# tests/unit.tftest.hcl

mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = ["us-east-1a", "us-east-1b", "us-east-1c"]
    }
  }
}

run "uses_all_availability_zones" {
  command = plan

  assert {
    condition     = length(aws_subnet.private) == 3
    error_message = "Should create subnet in each AZ"
  }
}
```

### Unit Tests

Unit tests use `command = plan` (the default):

- Do NOT create real resources
- Fast execution
- Test configuration logic, not cloud provider behavior

```hcl
run "unit_test_example" {
  command = plan  # Explicit, though it's the default

  assert {
    condition     = aws_instance.main.instance_type == var.instance_type
    error_message = "Instance type mismatch"
  }
}
```

### Integration Tests

Integration tests use `command = apply`:

- Create and destroy real resources
- Slower execution
- Test actual infrastructure behavior
- Require valid provider credentials

```hcl
run "integration_test_example" {
  command = apply  # Creates real resources

  assert {
    condition     = aws_instance.main.id != ""
    error_message = "Instance should be created"
  }
}
```

**Best Practice:** Run unit tests (`plan`) frequently during development. Run integration tests (`apply`) in CI or before releases.

### Running Tests

#### Basic Test Execution

```bash
# Run all tests in current directory
terraform test

# Run tests with verbose output
terraform test -verbose

# Run specific test file
terraform test -filter=tests/basic.tftest.hcl
```

#### CI Integration

```yaml
# .github/workflows/terraform-ci.yml (test job)
- name: Terraform Init
  run: terraform init

- name: Terraform Test
  run: terraform test -verbose
```

### What to Test

Tests **SHOULD** cover:

| Category | What to Test | Example |
| --- | --- | --- |
| **Variable validation** | Custom validation rules work correctly | Invalid environment rejected |
| **Computed values** | Locals and expressions compute correctly | CIDR calculations |
| **Resource configuration** | Resources have expected attributes | Instance type, tags |
| **Output values** | Outputs contain expected values | VPC ID not empty |
| **Module integration** | Modules work together | VPC + subnets + security groups |
| **Edge cases** | Boundary conditions | Zero instances, empty lists |

**Not to test:**

- Cloud provider behavior (e.g., "does AWS actually create an EC2?")
- Terraform core functionality
- External service availability

---

## Documentation Standards

### Module README Requirements

Every module **MUST** include a `README.md` with:

1. **Description** — What the module does
2. **Usage example** — Minimal working example
3. **Requirements** — Terraform and provider versions
4. **Inputs** — All variables with descriptions
5. **Outputs** — All outputs with descriptions

#### README Template

````markdown
# Module Name

Brief description of what this module creates.

## Usage

```hcl
module "example" {
  source = "./modules/example"

  required_variable = "value"
}
```

## Requirements

| Name | Version |
| --- | --- |
| terraform | >= 1.6.0 |
| aws | ~> 5.0 |

## Inputs

| Name | Description | Type | Default | Required |
| --- | --- | --- | --- | --- |
| required_variable | Description here | `string` | n/a | yes |
| optional_variable | Description here | `string` | `"default"` | no |

## Outputs

| Name | Description |
| --- | --- |
| output_name | Description of output |
````

**Note:** Consider using `terraform-docs` to generate input/output tables automatically.

### Inline Comment Conventions

Comments **SHOULD** explain "why," not "what."

#### Single-Line Comments

Use `#` for single-line comments:

```hcl
# Enable encryption to meet compliance requirements (SOC2)
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  # ...
}
```

#### Block Comments

Use `/* */` sparingly for multi-line explanations:

```hcl
/*
 * This security group allows inbound traffic from the corporate VPN.
 * CIDR ranges are managed by the network team and should not be
 * modified without their approval.
 */
resource "aws_security_group" "vpn_access" {
  # ...
}
```

### TODO Comment Format

Use standardized TODO format:

```hcl
# TODO(username): Migrate to new VPC module after v2.0 release
# TODO(team-name): Add support for IPv6 when available
```

---

## Pre-commit Discipline for Terraform

**⚠️ ALWAYS run pre-commit checks before committing Terraform code.**

Pre-commit hooks for Terraform **SHOULD** include:

1. `terraform fmt` — Format check
2. `terraform validate` — Syntax validation
3. `tflint` — Linting
4. Security scanning (optional but recommended)

### Workflow

1. Make Terraform changes
2. Run `terraform fmt -recursive`
3. Run `terraform validate`
4. Run pre-commit hooks: `pre-commit run --all-files`
5. Review and commit ALL auto-fixes as part of your change
6. Push to GitHub

**CI is a safety net, not a substitute for local checks.**

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml (Terraform section)
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.96.3
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
        args:
          - --args=--config=__GIT_WORKING_DIR__/.tflint.hcl
```

### CI Workflow Integration

This repository includes a comprehensive Terraform CI workflow at `.github/workflows/terraform-ci.yml` that enforces these standards automatically:

- **Format Check:** Runs `terraform fmt -check -recursive`
- **Validate:** Runs `terraform init` and `terraform validate` for all Terraform directories
- **Lint:** Runs TFLint with the repository's `.tflint.hcl` configuration
- **Test:** Runs `terraform test` for directories containing `.tftest.hcl` files

The CI workflow uses job dependencies to fail fast: format issues block validation, and validation issues block linting and testing.

For workflow customization options (such as enabling security scanning), see the comments in `.github/workflows/terraform-ci.yml`.

---

## "Done" Definition for Terraform Changes

A Terraform change is considered complete when:

### Code Quality

- [ ] All code passes `terraform fmt -check -recursive`
- [ ] All code passes `terraform validate`
- [ ] All code passes `tflint` without errors
- [ ] Pre-commit hooks pass

### Documentation

- [ ] All variables have `description` attributes
- [ ] All outputs have `description` attributes
- [ ] Sensitive variables/outputs are marked with `sensitive = true`
- [ ] Module `README.md` is updated (if applicable)

### Security

- [ ] No secrets appear in code or tfvars files
- [ ] State backend has encryption enabled
- [ ] IAM policies follow least-privilege
- [ ] Security scanning passes (if configured)

### Testing

- [ ] Variable validation rules are tested
- [ ] Critical outputs are tested
- [ ] Tests pass: `terraform test`

### Version Control

- [ ] `.terraform.lock.hcl` is committed
- [ ] State files are NOT committed
- [ ] All changes are committed with descriptive messages

### CI/CD

- [ ] CI pipeline passes
- [ ] Plan output reviewed (no unexpected changes)

---

## Scope Exceptions & Deviations from Standards

This section documents justified deviations from the standards defined in this document. When adopting this template, use this section to record exceptions specific to your organization, project, or deployment environment.

### How to Document Deviations

When a deviation from these standards is necessary, document it using the following format:

```markdown
#### [Short Description of Deviation]

- **Standard Affected:** [Link to or name of the standard being modified]
- **Reason:** [Business, technical, or organizational justification]
- **Scope:** [Which files, modules, or configurations are affected]
- **Approved By:** [Person or team who approved the deviation]
- **Date:** [YYYY-MM-DD]
- **Review Date:** [Optional: When this deviation should be reconsidered]
```

### Common Deviation Scenarios

The following are common scenarios where deviations may be justified:

- **Alternative Backend Workflows:** Using Terraform Cloud, Terraform Enterprise, Spacelift, or other orchestration tools instead of `backend.tf`. Document which backend sections do not apply.
- **Provider-Specific Requirements:** Organization policies that mandate specific provider configurations (e.g., required regions, mandatory tags beyond those listed).
- **Legacy Compatibility:** Maintaining compatibility with older Terraform versions or modules that cannot be immediately updated.
- **Organizational Naming Conventions:** Pre-existing naming conventions that conflict with this template but are required for consistency with other systems.
- **Security Policy Overrides:** Stricter security requirements that go beyond or differ from those specified here.

### Recorded Deviations

> **Note:** Replace the examples below with actual deviations for your project, or remove this section if no deviations apply.

*No deviations recorded yet. When deviations are necessary, document them here using the format above.*
