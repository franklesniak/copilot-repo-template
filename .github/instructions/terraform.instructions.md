---
applyTo: "**/*.tf,**/*.tfvars,**/*.tftest.hcl,**/*.tf.json,**/*.tftpl,**/*.tfbackend"
description: "Terraform coding standards: secure, modular, and well-documented infrastructure as code."
---

# Terraform Writing Style

**Version:** 1.6.20260130.0

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-01-30
- **Scope:** Defines Terraform coding standards for all `.tf`, `.tfvars`, `.tftest.hcl`, `.tf.json`, `.tftpl`, and `.tfbackend` files in this repository. Covers style, formatting, naming conventions, file organization, variable and output design, resource configuration, module design, refactoring, state management, security best practices, provider management, testing, and documentation requirements.
- **Related:** [Repository Copilot Instructions](../copilot-instructions.md)

## Table of Contents

- [Keywords](#keywords)
- [Quick Reference Checklist](#quick-reference-checklist)
- [Placeholder Convention (`REPLACE_ME_*`)](#placeholder-convention-replace_me_)
- [Executive Summary: Terraform Philosophy](#executive-summary-terraform-philosophy)
- [Formatting and Style](#formatting-and-style)
- [Naming Conventions](#naming-conventions)
- [File Organization](#file-organization)
- [Variable and Output Design](#variable-and-output-design)
  - [Nullable Variables](#nullable-variables)
  - [Terraform Cloud Variable Precedence](#terraform-cloud-variable-precedence)
- [Continuous Validation with check Blocks](#continuous-validation-with-check-blocks)
- [Resource Configuration](#resource-configuration)
- [Module Design](#module-design)
- [Refactoring](#refactoring)
- [State Management](#state-management)
  - [Resource Targeting](#resource-targeting)
- [Provider Management](#provider-management)
  - [Provider Aliasing](#provider-aliasing)
- [Security Best Practices](#security-best-practices)
  - [Sensitive Values in Meta-Arguments](#sensitive-values-in-meta-arguments)
- [Testing with Terraform Test](#testing-with-terraform-test)
- [Documentation Standards](#documentation-standards)
- [Pre-commit Discipline for Terraform](#pre-commit-discipline-for-terraform)
- ["Done" Definition for Terraform Changes](#done-definition-for-terraform-changes)
- [Related Documentation](#related-documentation)
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
- **[All]** Template files **SHOULD** use `.tftpl` extension → [Template Files (.tftpl)](#template-files-tftpl)
- **[All]** Template files **SHOULD** be placed in a `templates/` subdirectory → [Template Files (.tftpl)](#template-files-tftpl)

### Variable and Output Design

- **[All]** Variables **MUST** include a `description` → [Variable Documentation Requirements](#variable-documentation-requirements)
- **[All]** Variables **MUST** include explicit `type` constraint → [Variable Type Constraints](#variable-type-constraints)
- **[All]** Optional variables **MUST** have a `default` value → [Variable Defaults](#variable-defaults)
- **[All]** Sensitive variables **MUST** be marked with `sensitive = true` → [Sensitive Variable Marking](#sensitive-variable-marking)
- **[All]** Variables with constrained values **SHOULD** use `validation` blocks → [Variable Validation](#variable-validation)
- **[All]** Outputs **MUST** include a `description` → [Output Documentation Requirements](#output-documentation-requirements)
- **[All]** Sensitive outputs **MUST** be marked with `sensitive = true` → [Sensitive Output Marking](#sensitive-output-marking)
- **[All]** Variables **SHOULD** explicitly set `nullable` to document null-handling behavior → [Nullable Variables](#nullable-variables)

### Continuous Validation

- **[All]** `check` blocks **MAY** be used for continuous validation → [Continuous Validation with check Blocks](#continuous-validation-with-check-blocks)

### Resource Configuration

- **[All]** Meta-arguments **MUST** appear first in resource blocks → [Meta-Argument Ordering](#meta-argument-ordering)
- **[All]** Required arguments **MUST** appear before optional arguments → [Argument Ordering](#argument-ordering)
- **[All]** Nested blocks **MUST** appear last in resource blocks → [Nested Block Placement](#nested-block-placement)
- **[All]** Resources **MUST** include required tags → [Required Tags](#required-tags)
- **[Root]** Provider-level default tags **SHOULD** be configured → [Default Tags Configuration](#default-tags-configuration)
- **[All]** Local values **SHOULD** be used for computed or merged tags → [Local Tags Pattern](#local-tags-pattern)
- **[All]** `precondition` blocks **SHOULD** validate assumptions before resource creation → [Resource Preconditions](#resource-preconditions)
- **[All]** `postcondition` blocks **SHOULD** validate resource state after creation → [Resource Postconditions](#resource-postconditions)
- **[All]** `depends_on` **SHOULD** be avoided unless dependencies are not inferable → [Explicit Dependencies](#explicit-dependencies)
- **[All]** `for_each` **SHOULD** be preferred over `count` for collections → [for_each vs count](#for_each-vs-count)
- **[All]** Dynamic blocks **SHOULD** be used sparingly → [Dynamic Blocks](#dynamic-blocks)
- **[All]** `prevent_destroy` **SHOULD** be used for critical resources → [Lifecycle Block Options](#lifecycle-block-options)
- **[All]** `ignore_changes` **SHOULD** be used for attributes managed outside Terraform → [Lifecycle Block Options](#lifecycle-block-options)

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
- **[All]** `terraform apply -target` **SHOULD NOT** be used in normal workflows → [Resource Targeting](#resource-targeting)

### Provider Management

- **[All]** Provider versions **MUST** be constrained → [Provider Version Constraints](#provider-version-constraints)
- **[All]** `.terraform.lock.hcl` **MUST** be committed to version control → [Lock File Management](#lock-file-management)
- **[All]** Pessimistic constraint operator (`~>`) **SHOULD** be used for providers → [Pessimistic Constraints](#pessimistic-constraints)
- **[All]** Multi-region or multi-account deployments **MUST** use provider aliases → [Provider Aliasing](#provider-aliasing)

### Security

- **[All]** Secrets **MUST NOT** appear in `.tf` files → [Secret Management](#secret-management)
- **[All]** Secrets **MUST NOT** have default values → [No Secret Defaults](#no-secret-defaults)
- **[All]** Secrets **MUST** be provided via environment variables or secret managers → [Approved Secret Patterns](#approved-secret-patterns)
- **[Root]** State backends **MUST** enable encryption → [State Security](#state-security)
- **[All]** IAM policies **MUST** follow least-privilege principles → [Least-Privilege Principles](#least-privilege-principles)
- **[All]** Wildcard actions **SHOULD NOT** be used in IAM policies → [IAM Policy Guidelines](#iam-policy-guidelines)
- **[All]** Sensitive values **MUST NOT** be used in `for_each` or `count` expressions → [Sensitive Values in Meta-Arguments](#sensitive-values-in-meta-arguments)

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
- **[All]** Authors **MUST** use placeholder markers following the `REPLACE_ME_*` pattern for values that require customization → [Placeholder Convention](#placeholder-convention-replace_me_)

## Placeholder Convention (`REPLACE_ME_*`)

This document uses the `REPLACE_ME_*` placeholder convention for values that **MUST** be customized before use. This convention applies across all cloud providers (AWS, Azure, GCP) and ensures that examples remain portable while clearly identifying required customizations.

### Purpose

Placeholders serve multiple purposes:

- **Safety:** Prevent accidental deployment of example values to production
- **Clarity:** Clearly identify which values require organization-specific configuration
- **Searchability:** Enable easy discovery of all values requiring customization via `grep -r "REPLACE_ME"`
- **Consistency:** Provide a uniform approach across all examples regardless of provider

### Standard Placeholders

The following standard placeholders **SHOULD** be used consistently throughout this document and in derived configurations:

| Placeholder | Description | Example Replacement |
| --- | --- | --- |
| `REPLACE_ME_REGION` | Cloud provider region | `us-east-1`, `eastus`, `us-central1` |
| `REPLACE_ME_STATE_BUCKET` | State storage bucket/container name | `my-org-terraform-state` |
| `REPLACE_ME_LOCK_TABLE` | State locking table (AWS DynamoDB) | `terraform-locks` |
| `REPLACE_ME_RESOURCE_GROUP` | Azure resource group name | `rg-terraform-state` |
| `REPLACE_ME_STORAGE_ACCOUNT` | Azure storage account name | `stterraformstate` |
| `REPLACE_ME_CONTAINER` | Azure blob container name | `tfstate` |
| `REPLACE_ME_PROJECT_ID` | GCP project ID | `my-gcp-project-123` |
| `REPLACE_ME_ORG` | Terraform Cloud/Enterprise organization | `my-organization` |
| `REPLACE_ME_WORKSPACE` | Terraform Cloud/Enterprise workspace | `prod-infrastructure` |
| `REPLACE_ME_INSTANCE_ID` | Cloud instance/resource ID for imports | `i-1234567890abcdef0` |
| `REPLACE_ME_AMI_ID` | AWS AMI ID | `ami-0abcdef1234567890` |
| `REPLACE_ME_INSTANCE_TYPE` | Cloud instance/VM type | `t3.micro`, `Standard_B1s`, `e2-micro` |
| `REPLACE_ME_SUBSCRIPTION_ID` | Azure subscription ID | `00000000-0000-0000-0000-000000000000` |
| `REPLACE_ME_TENANT_ID` | Azure tenant ID | `00000000-0000-0000-0000-000000000000` |
| `REPLACE_ME_PRIMARY_BUCKET` | Primary storage bucket name | `my-org-primary-bucket` |
| `REPLACE_ME_REPLICA_BUCKET` | Replica storage bucket name | `my-org-replica-bucket` |
| `REPLACE_ME_EUROPE_BUCKET` | Europe region bucket name | `my-org-europe-bucket` |
| `REPLACE_ME_PRIMARY_STORAGE` | Primary Azure storage account name | `stprimarystorage` |
| `REPLACE_ME_SECONDARY_STORAGE` | Secondary Azure storage account name | `stsecondarystorage` |
| `REPLACE_ME_KEYVAULT_NAME` | Azure Key Vault name | `kv-my-org-secrets` |
| `REPLACE_ME_SECRET_NAME` | Secret name in secret manager | `database-password` |
| `REPLACE_ME_VAULT_SECRET_PATH` | HashiCorp Vault secret path | `secret/data/database` |
| `REPLACE_ME_PRIMARY_REGION` | Primary cloud provider region | `us-east-1`, `eastus`, `us-central1` |
| `REPLACE_ME_WEST_REGION` | West/secondary region (AWS) | `us-west-2` |
| `REPLACE_ME_EU_REGION` | Europe region (AWS) | `eu-west-1` |
| `REPLACE_ME_EUROPE_REGION` | Europe region (GCP) | `europe-west1` |
| `REPLACE_ME_SECONDARY_REGION` | Secondary region | `us-west-2`, `westus2`, `us-west1` |

### Usage Rules

- **[All]** Authors **MUST** use `REPLACE_ME_*` placeholders for values that require customization
- **[All]** Placeholder names **MUST** use `UPPER_SNAKE_CASE` with the `REPLACE_ME_` prefix
- **[All]** Placeholder names **SHOULD** be descriptive (e.g., `REPLACE_ME_STATE_BUCKET` not `REPLACE_ME_BUCKET`)
- **[All]** When adopting configurations, search for all placeholders using `grep -r "REPLACE_ME"` and replace with actual values
- **[All]** Production code **MUST NOT** contain any `REPLACE_ME_*` placeholders

### Provider-Specific Notes

This document provides examples for multiple cloud providers (AWS, Azure, GCP). When examples include provider-specific placeholders, each provider's version is labeled accordingly. For step-by-step guidance and a checklist for removing examples for providers you do not use, see the [Copilot Terraform Instructions Configuration](../../OPTIONAL_CONFIGURATIONS.md#copilot-terraform-instructions-configuration) guide. If you remove or substantially alter provider examples, record this as a documented deviation following the [Scope Exceptions & Deviations from Standards](#scope-exceptions--deviations-from-standards) section.

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

**AWS Example:**

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

**Azure Example:**

```hcl
# versions.tf

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}
```

**GCP Example:**

```hcl
# versions.tf

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}
```

### Provider Configuration File

Root modules **MUST** have a `providers.tf` file with provider configuration:

**AWS Example:**

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

**Azure Example:**

```hcl
# providers.tf

provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
}
```

> **Note:** Azure does not support provider-level default tags. Use the `azurerm_resource_group` or resource-level `tags` blocks consistently across resources.

**GCP Example:**

```hcl
# providers.tf

provider "google" {
  project = var.project_id
  region  = var.region
}
```

> **Note:** GCP supports `default_labels` at the provider level (Google provider 4.x+), but label keys must be lowercase. For consistent lowercase enforcement or cross-provider compatibility, consider using a `locals` block for common labels.

### Backend Configuration

Root modules **MUST** configure a remote backend, either in `backend.tf` or within the `terraform` block:

**AWS Example:**

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

**Azure Example:**

```hcl
# backend.tf

terraform {
  backend "azurerm" {
    resource_group_name  = "REPLACE_ME_RESOURCE_GROUP"
    storage_account_name = "REPLACE_ME_STORAGE_ACCOUNT"
    container_name       = "REPLACE_ME_CONTAINER"
    key                  = "environments/prod/terraform.tfstate"
  }
}
```

**GCP Example:**

```hcl
# backend.tf

terraform {
  backend "gcs" {
    bucket = "REPLACE_ME_STATE_BUCKET"
    prefix = "environments/prod"
  }
}
```

#### Partial Backend Configuration

As an alternative to placeholder values, Terraform supports **partial backend configuration**. This pattern separates static configuration (committed to version control) from dynamic values (provided at runtime):

**AWS Backend file (committed):**

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

**AWS Backend config file (environment-specific):**

```hcl
# config/prod.s3.tfbackend

bucket         = "my-org-terraform-state"
region         = "us-east-1"
dynamodb_table = "terraform-locks"
```

**Azure Backend file (committed):**

```hcl
# backend.tf - partial configuration

terraform {
  backend "azurerm" {
    key = "environments/prod/terraform.tfstate"
    # resource_group_name, storage_account_name, container_name provided via -backend-config
  }
}
```

**Azure Backend config file (environment-specific):**

```hcl
# config/prod.azurerm.tfbackend

resource_group_name  = "REPLACE_ME_RESOURCE_GROUP"
storage_account_name = "REPLACE_ME_STORAGE_ACCOUNT"
container_name       = "REPLACE_ME_CONTAINER"
```

**GCP Backend file (committed):**

```hcl
# backend.tf - partial configuration

terraform {
  backend "gcs" {
    prefix = "environments/prod"
    # bucket provided via -backend-config
  }
}
```

**GCP Backend config file (environment-specific):**

```hcl
# config/prod.gcs.tfbackend

bucket = "REPLACE_ME_STATE_BUCKET"
```

**Usage:**

```bash
terraform init -backend-config=config/prod.s3.tfbackend      # AWS
terraform init -backend-config=config/prod.azurerm.tfbackend  # Azure
terraform init -backend-config=config/prod.gcs.tfbackend      # GCP
```

This pattern is useful when:

- Backend values vary by environment but the state key structure is consistent
- Teams prefer runtime configuration over placeholder replacement
- CI/CD pipelines inject backend configuration dynamically

Both the [`REPLACE_ME_*` placeholder pattern](#placeholder-convention-replace_me_) and partial configuration pattern are valid approaches. Choose the pattern that best fits your team's workflow.

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

### Terraform Cloud Variable Precedence

When using Terraform Cloud or Terraform Enterprise, variables can be set at multiple levels. The precedence order (highest to lowest) is:

1. `-var` and `-var-file` flags in CLI-driven runs
2. `*.auto.tfvars` files (in alphabetical order)
3. `terraform.tfvars` (if present)
4. Workspace-specific variables (set in Terraform Cloud UI/API)
5. Variable sets (shared across workspaces)
6. Environment variables (`TF_VAR_*`)
7. `default` values in variable declarations

**Note:** In Terraform Cloud, workspace variables and variable sets take precedence over environment variables (`TF_VAR_*`). This differs from local Terraform execution where environment variables have higher precedence.

Document which variable management approach your organization uses in the [Scope Exceptions](#scope-exceptions--deviations-from-standards) section to ensure consistency across team members.

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

### Template Files (.tftpl)

Template files are used with the `templatefile()` function to generate dynamic content such as configuration files, scripts, or policy documents. Template files **SHOULD** follow these conventions:

- Template files **SHOULD** use the `.tftpl` extension for clear identification
- Template files **SHOULD** be placed in a `templates/` subdirectory within the module or root configuration
- Template file variables **SHOULD** be documented at the top of the template file using comments

**Directory structure:**

```text
modules/
└── <module-name>/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    └── templates/
        ├── user_data.sh.tftpl
        └── policy.json.tftpl
```

**Template file example with documentation:**

```tftpl
#!/bin/bash
# Template: user_data.sh.tftpl
# Variables:
#   - environment: Deployment environment (string)
#   - app_name: Application name (string)
#   - enable_monitoring: Whether to enable monitoring (bool)

echo "Deploying ${app_name} to ${environment}"

%{ if enable_monitoring ~}
echo "Monitoring enabled"
%{ endif ~}
```

**Using templatefile() function:**

```hcl
resource "aws_instance" "main" {
  ami           = var.ami_id
  instance_type = var.instance_type

  user_data = templatefile("${path.module}/templates/user_data.sh.tftpl", {
    environment       = var.environment
    app_name          = var.app_name
    enable_monitoring = var.enable_monitoring
  })
}
```

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

### Nullable Variables

The `nullable` attribute (Terraform 1.1+) controls whether a variable can accept `null` as a valid value. By default, all variables have `nullable = true`, meaning they can accept `null` values.

**Purpose:**

- Explicitly allow or disallow `null` as a valid value
- Distinguish between "not provided" and "explicitly set to null"
- Improve input validation for required values

**When to use explicit `nullable`:**

- Use `nullable = true` when `null` is a meaningful value distinct from the default
- Use `nullable = false` when `null` values **MUST** be rejected

**Example:**

```hcl
variable "optional_cidr" {
  description = "Optional secondary CIDR block. Set to null to skip configuration."
  type        = string
  default     = null
  nullable    = true  # Explicitly allow null values
}

variable "required_name" {
  description = "Required resource name. Cannot be null."
  type        = string
  nullable    = false  # Null values will be rejected
}
```

**Usage pattern:**

```hcl
resource "aws_vpc_ipv4_cidr_block_association" "secondary" {
  count = var.optional_cidr != null ? 1 : 0

  vpc_id     = aws_vpc.main.id
  cidr_block = var.optional_cidr
}
```

---

## Continuous Validation with check Blocks

The `check` block (Terraform 1.5+) provides a mechanism for continuous validation assertions that run on every `plan` and `apply` operation. Unlike `precondition` and `postcondition` blocks, `check` blocks produce **warning diagnostics** that do **not** halt execution when assertions fail.

### When to Use check Blocks

`check` blocks **MAY** be used for deterministic validations that rely only on Terraform configuration, state, and resource attributes, such as:

- **Policy conformance:** Ensure resources comply with tagging, encryption, and sizing standards
- **Configuration invariants:** Assert relationships between resources (for example, capacity, counts, or naming patterns)
- **Drift and safety nets:** Highlight situations where the actual infrastructure shape no longer matches declared expectations

In this repository, `check` block `assert` conditions **MUST** be deterministic and **MUST NOT** introduce network calls or depend on live external service reachability. Use dedicated observability/monitoring tooling for runtime health checks and external dependency validation.

### check Block Syntax

```hcl
check "alb_has_listeners" {
  assert {
    condition     = length(aws_lb_listener.app) > 0
    error_message = "Application load balancer must have at least one listener configured."
  }
}
```

### Comparison with precondition/postcondition

| Feature | `check` blocks | `precondition`/`postcondition` |
| --- | --- | --- |
| **Causes failure** | No (warning only) | Yes (error) |
| **Runs during** | Every plan/apply | Resource creation/update |
| **Scope** | Configuration-wide | Resource-specific |
| **Use case** | Ongoing invariant checks | Input/output validation |

### Best Practices

- **Bounded usage:** Each module **SHOULD** define at most 3 `check` blocks and **SHOULD** reserve them for critical invariants (for example, cross-resource consistency or security posture), not routine validation that can be handled with `precondition`/`postcondition`.
- **Deterministic and cheap assertions:** `condition` expressions **MUST** be deterministic (no dependence on current time, randomness, or external services) and **MUST NOT** introduce additional network calls (for example, avoid `http` or other remote data sources inside a `check` block). They **SHOULD** only reference values already available during planning (resource attributes, variables, locals, and data sources the plan already needs).
- **Constrained complexity:** Assertions **SHOULD** be expressed as a small number of boolean expressions combined with `&&`/`||`, and **SHOULD NOT** iterate over large collections or use deeply nested conditionals that materially increase plan/apply latency.
- **Document purpose:** `error_message` values **MUST** clearly state which invariant failed and what the operator **SHOULD** do next (for example, "rotate API token X" or "scale service Y").

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

**AWS Example:**

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

> **Note:** Azure does not support provider-level default tags. GCP supports `default_labels` at the provider level (Google provider 4.x+), but label keys must be lowercase. For Azure, use a `locals` block to define common tags. For GCP, you may use `default_labels` or a `locals` block if you need consistent lowercase key enforcement. See the [Local Tags Pattern](#local-tags-pattern) section below.

### Local Tags Pattern

Use locals for computed or merged tags. This pattern is **REQUIRED** for Azure (no provider-level support) and **RECOMMENDED** for GCP when consistent lowercase label key enforcement is needed:

**AWS/Azure Example (Tags):**

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

**GCP Example (Labels - lowercase keys required):**

```hcl
locals {
  # GCP labels must use lowercase keys
  common_labels = {
    name        = "${var.project_name}-${var.environment}"
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
  }

  # Merge common labels with resource-specific labels
  instance_labels = merge(local.common_labels, {
    role = "web-server"
  })
}
```

> **Note:** GCP label keys must be lowercase and can only contain lowercase letters, numeric characters, underscores, and dashes. AWS and Azure tags support mixed-case keys.

**Azure Example - Applying local tags to resources:**

```hcl
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location
  tags     = local.common_tags
}
```

**GCP Example - Applying local labels to resources:**

```hcl
resource "google_compute_instance" "main" {
  name         = "${var.project_name}-${var.environment}"
  machine_type = var.machine_type
  zone         = var.zone

  labels = local.common_labels
}
```

### Lifecycle Validation

Terraform 1.2+ introduced `precondition` and `postcondition` blocks within the `lifecycle` block, enabling resource-level validation of assumptions and outcomes.

#### Resource Preconditions

`precondition` blocks **SHOULD** validate assumptions before resource creation. Use them to ensure that related resources or variables meet requirements before Terraform attempts to create or modify a resource.

```hcl
resource "aws_instance" "main" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    precondition {
      condition     = var.environment != "prod" || var.enable_monitoring
      error_message = "Production instances must have monitoring enabled."
    }
  }
}
```

**Use cases for preconditions:**

- Validating cross-resource dependencies
- Enforcing business rules that span multiple variables
- Ensuring prerequisites are met before expensive operations

#### Resource Postconditions

`postcondition` blocks **SHOULD** validate resource state after creation. Use them to ensure that computed values meet expectations after Terraform creates or modifies a resource.

```hcl
resource "aws_instance" "main" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    postcondition {
      condition     = self.public_ip != null
      error_message = "Instance must have a public IP assigned."
    }
  }
}
```

**Use cases for postconditions:**

- Validating computed attributes (IPs, ARNs, generated names)
- Ensuring provider-side defaults meet expectations
- Catching unexpected resource configurations

### Lifecycle Block Options

The `lifecycle` block supports several meta-argument options beyond `precondition` and `postcondition` for controlling resource behavior. The following table summarizes these lifecycle meta-arguments:

| Option | Purpose | Use Case |
| --- | --- | --- |
| `create_before_destroy` | Create replacement before destroying original | Zero-downtime replacements |
| `prevent_destroy` | Prevent accidental resource deletion | Protect critical production resources |
| `ignore_changes` | Ignore changes to specific attributes | Attributes managed outside Terraform |
| `replace_triggered_by` | Force replacement when dependencies change | Trigger replacement on related resource changes (Terraform 1.2+) |

#### When to Use Each Option

**`create_before_destroy`:** Use when replacing a resource must not cause downtime. The new resource is created first, then the old one is destroyed.

**`prevent_destroy`:** Use for critical resources that **MUST NOT** be accidentally deleted, such as production databases, state storage buckets, or encryption keys.

**`ignore_changes`:** Use when an attribute is intentionally managed outside Terraform (e.g., auto-scaling group desired capacity, tags managed by external tools).

**`replace_triggered_by`:** Use when a resource **SHOULD** be replaced whenever a related resource changes, even if no direct attributes are affected.

#### Example: Protecting a Critical Resource

```hcl
# Protect production database from accidental deletion
resource "aws_db_instance" "production" {
  identifier     = "prod-database"
  engine         = "postgres"
  instance_class = var.db_instance_class
  # ... other configuration

  lifecycle {
    prevent_destroy = true
  }
}

# Protect Terraform state bucket
resource "aws_s3_bucket" "terraform_state" {
  bucket = "my-org-terraform-state"

  lifecycle {
    prevent_destroy = true
  }
}
```

#### Example: Ignoring External Changes

```hcl
# Ignore changes to tags managed by AWS Config or other external tools
resource "aws_instance" "main" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    ignore_changes = [
      tags["LastScannedBy"],
      tags["ComplianceStatus"],
    ]
  }
}
```

### Explicit Dependencies

Terraform automatically infers dependencies from resource references. The `depends_on` meta-argument **SHOULD** be avoided unless dependencies are not inferable from the configuration.

#### When depends_on is Appropriate

`depends_on` **SHOULD** only be used for:

- **Hidden dependencies:** When a resource depends on another resource's side effects (e.g., IAM policy propagation delays)
- **Module dependencies:** When a module depends on another module's resources without direct references
- **Timing issues:** When the order of operations matters but isn't reflected in resource attributes

#### Anti-pattern: Redundant depends_on

```hcl
# BAD: Unnecessary depends_on - dependency is already inferred from the reference
resource "aws_instance" "main" {
  subnet_id  = aws_subnet.main.id
  depends_on = [aws_subnet.main]  # Redundant
}

# GOOD: Dependency is implicit from the reference
resource "aws_instance" "main" {
  subnet_id = aws_subnet.main.id
}
```

#### Legitimate Use Case

```hcl
# GOOD: Hidden dependency on IAM role policy attachment
resource "aws_instance" "main" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  iam_instance_profile = aws_iam_instance_profile.main.name

  # The instance profile references the role, but doesn't reference the policy attachment.
  # Without depends_on, the instance may launch before the policy is attached.
  depends_on = [aws_iam_role_policy_attachment.main]
}
```

### for_each vs count

When creating multiple instances of a resource, `for_each` **SHOULD** be preferred over `count` for collections where resources have unique identifiers.

#### Comparison Table

| Use `for_each` when... | Use `count` when... |
| --- | --- |
| Resources have unique identifiers | Simple on/off toggle (`count = var.enabled ? 1 : 0`) |
| Order doesn't matter | Resources are truly identical and ordered |
| Items may be added/removed from middle of collection | Only adding/removing from the end |
| Each resource is addressable by key | Index-based addressing is acceptable |

#### Why for_each is Preferred

Removing an item from a `count`-based list causes all subsequent resources to be recreated due to index shifting. `for_each` uses map keys, so only the specific resource is affected.

```hcl
# BAD: Using count with a list - removing any item shifts all subsequent indices
resource "aws_instance" "servers" {
  count         = length(var.server_names)
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  tags = {
    Name = var.server_names[count.index]
  }
}

# GOOD: Using for_each with a set - removing "server-b" only affects that resource
resource "aws_instance" "servers" {
  for_each      = toset(var.server_names)
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  tags = {
    Name = each.value
  }
}
```

#### When count is Appropriate

```hcl
# GOOD: count for conditional resource creation
resource "aws_cloudwatch_log_group" "main" {
  count = var.enable_logging ? 1 : 0
  name  = "/app/${var.environment}"
}
```

### Dynamic Blocks

Dynamic blocks allow generating multiple nested blocks from a collection. They **SHOULD** be used sparingly because they reduce readability and complicate debugging.

#### When to Use Dynamic Blocks

Use dynamic blocks when:

- The number of nested blocks is variable and determined by configuration
- The block structure is repetitive and follows a consistent pattern
- Manual repetition would create maintenance burden

```hcl
# GOOD: Variable number of ingress rules from configuration
resource "aws_security_group" "main" {
  name        = "${var.project_name}-sg"
  description = "Security group for ${var.project_name}"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
```

#### When to Avoid Dynamic Blocks

Avoid dynamic blocks when the number of blocks is fixed and small. Writing explicit blocks improves readability:

```hcl
# GOOD: Fixed, small number of rules - explicit is clearer
resource "aws_security_group" "web" {
  name        = "${var.project_name}-web-sg"
  description = "Web security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# AVOID: Using dynamic for only 2-3 fixed rules adds unnecessary complexity
# dynamic "ingress" { ... }
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

**AWS Example:**

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

**Azure Example:**

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "REPLACE_ME_RESOURCE_GROUP"
    storage_account_name = "REPLACE_ME_STORAGE_ACCOUNT"
    container_name       = "REPLACE_ME_CONTAINER"
    key                  = "environments/prod/terraform.tfstate"
  }
}
```

**GCP Example:**

```hcl
terraform {
  backend "gcs" {
    bucket = "REPLACE_ME_STATE_BUCKET"
    prefix = "environments/prod"
  }
}
```

> **Placeholder Values:** The examples above use placeholder values (e.g., `REPLACE_ME_STATE_BUCKET`). Replace these with your organization's actual values when adopting this template. See [Placeholder Convention](#placeholder-convention-replace_me_) for the complete list of standard placeholders.

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

**AWS Example:**

```hcl
# S3 backend with encryption
terraform {
  backend "s3" {
    bucket  = "REPLACE_ME_STATE_BUCKET"
    key     = "prod/terraform.tfstate"
    region  = "REPLACE_ME_REGION"
    encrypt = true  # REQUIRED
  }
}
```

**Azure Example:**

```hcl
# Azure Storage backend (encryption is enabled by default on Azure Storage accounts)
terraform {
  backend "azurerm" {
    resource_group_name  = "REPLACE_ME_RESOURCE_GROUP"
    storage_account_name = "REPLACE_ME_STORAGE_ACCOUNT"
    container_name       = "REPLACE_ME_CONTAINER"
    key                  = "prod/terraform.tfstate"
  }
}
```

> **Note:** Azure Storage accounts have encryption enabled by default. Ensure your storage account is configured with appropriate encryption settings.

**GCP Example:**

```hcl
# GCS backend (encryption is enabled by default on GCS buckets)
terraform {
  backend "gcs" {
    bucket = "REPLACE_ME_STATE_BUCKET"
    prefix = "prod"
  }
}
```

> **Note:** GCS buckets are encrypted by default using Google-managed encryption keys. For additional security, configure Customer-Managed Encryption Keys (CMEK).

### State Locking

State backends **MUST** support and enable state locking:

**AWS Example:**

```hcl
# S3 backend with DynamoDB locking
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

**Azure Example:**

```hcl
# Azure Storage backend (locking is built-in via blob leases)
terraform {
  backend "azurerm" {
    resource_group_name  = "REPLACE_ME_RESOURCE_GROUP"
    storage_account_name = "REPLACE_ME_STORAGE_ACCOUNT"
    container_name       = "REPLACE_ME_CONTAINER"
    key                  = "prod/terraform.tfstate"
  }
}
```

> **Note:** Azure Storage backend uses blob leases for state locking automatically. No additional configuration is required.

**GCP Example:**

```hcl
# GCS backend (locking is built-in)
terraform {
  backend "gcs" {
    bucket = "REPLACE_ME_STATE_BUCKET"
    prefix = "prod"
  }
}
```

> **Note:** GCS backend supports state locking natively. No additional configuration is required.

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

### Resource Targeting

`terraform apply -target` **SHOULD NOT** be used in normal workflows. Resource targeting:

- Creates state drift between targeted and non-targeted resources
- Can leave infrastructure in inconsistent states
- Bypasses dependency validation

Resource targeting is intended **only** for exceptional recovery scenarios where a specific resource must be modified in isolation.

**If targeting is needed regularly**, this indicates the configuration is too large. Split the configuration into smaller, independent modules that can be applied separately.

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

### Provider Aliasing

Provider aliasing enables multiple instances of the same provider for multi-region or multi-account deployments. Use aliases when resources need to be created in different regions, accounts, or with different configurations.

**Common use cases:**

- Disaster recovery across regions
- Cross-region replication (S3, RDS, etc.)
- Multi-account architectures
- Resources requiring different provider configurations

**AWS Example - Defining aliased providers:**

```hcl
# providers.tf

provider "aws" {
  region = "REPLACE_ME_PRIMARY_REGION"  # e.g., us-east-1
  # Default provider (no alias)
}

provider "aws" {
  alias  = "west"
  region = "REPLACE_ME_WEST_REGION"  # e.g., us-west-2
}

provider "aws" {
  alias  = "eu"
  region = "REPLACE_ME_EU_REGION"  # e.g., eu-west-1
}
```

**AWS Example - Using aliased providers in resources:**

```hcl
# Use default provider
resource "aws_s3_bucket" "primary" {
  bucket = "REPLACE_ME_PRIMARY_BUCKET"
}

# Use aliased provider
resource "aws_s3_bucket" "replica" {
  provider = aws.west
  bucket   = "REPLACE_ME_REPLICA_BUCKET"
}
```

**Azure Example - Defining aliased providers:**

```hcl
# providers.tf

provider "azurerm" {
  features {}
  subscription_id = var.primary_subscription_id
  # Default provider (no alias)
}

provider "azurerm" {
  alias           = "secondary"
  features {}
  subscription_id = var.secondary_subscription_id
}
```

**Azure Example - Using aliased providers in resources:**

```hcl
# Use default provider
resource "azurerm_storage_account" "primary" {
  name                     = "REPLACE_ME_PRIMARY_STORAGE"
  resource_group_name      = azurerm_resource_group.primary.name
  location                 = azurerm_resource_group.primary.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# Use aliased provider
resource "azurerm_storage_account" "secondary" {
  provider                 = azurerm.secondary
  name                     = "REPLACE_ME_SECONDARY_STORAGE"
  resource_group_name      = azurerm_resource_group.secondary.name
  location                 = azurerm_resource_group.secondary.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
```

**GCP Example - Defining aliased providers:**

```hcl
# providers.tf

provider "google" {
  project = var.primary_project_id
  region  = "REPLACE_ME_PRIMARY_REGION"  # e.g., us-central1
  # Default provider (no alias)
}

provider "google" {
  alias   = "europe"
  project = var.primary_project_id
  region  = "REPLACE_ME_EUROPE_REGION"  # e.g., europe-west1
}

provider "google" {
  alias   = "secondary_project"
  project = var.secondary_project_id
  region  = "REPLACE_ME_SECONDARY_REGION"  # e.g., us-central1
}
```

**GCP Example - Using aliased providers in resources:**

```hcl
# Use default provider
resource "google_storage_bucket" "primary" {
  name     = "REPLACE_ME_PRIMARY_BUCKET"
  location = "US"
}

# Use aliased provider for different region
resource "google_storage_bucket" "europe" {
  provider = google.europe
  name     = "REPLACE_ME_EUROPE_BUCKET"
  location = "EU"
}
```

**Passing providers to modules:**

```hcl
module "vpc_west" {
  source = "./modules/vpc"

  providers = {
    aws = aws.west
  }

  cidr_block = "10.1.0.0/16"
}
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
# Choose one of the following exports based on your cloud provider:

# AWS
export TF_VAR_db_password="$(aws secretsmanager get-secret-value --secret-id REPLACE_ME_SECRET_NAME --query SecretString --output text)"

# Azure
export TF_VAR_db_password="$(az keyvault secret show --vault-name REPLACE_ME_KEYVAULT_NAME --name REPLACE_ME_SECRET_NAME --query value -o tsv)"

# GCP
export TF_VAR_db_password="$(gcloud secrets versions access latest --secret=REPLACE_ME_SECRET_NAME)"

# Then run terraform apply
terraform apply
```

**Pattern 2: Cloud Provider Secret Managers**

**AWS Example - Secrets Manager:**

```hcl
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "REPLACE_ME_SECRET_NAME"
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}
```

**Azure Example - Key Vault:**

```hcl
data "azurerm_key_vault" "main" {
  name                = "REPLACE_ME_KEYVAULT_NAME"
  resource_group_name = "REPLACE_ME_RESOURCE_GROUP"
}

data "azurerm_key_vault_secret" "db_password" {
  name         = "REPLACE_ME_SECRET_NAME"
  key_vault_id = data.azurerm_key_vault.main.id
}

resource "azurerm_mssql_server" "main" {
  administrator_login_password = data.azurerm_key_vault_secret.db_password.value
  # ... other configuration
}
```

**GCP Example - Secret Manager:**

```hcl
data "google_secret_manager_secret_version" "db_password" {
  secret  = "REPLACE_ME_SECRET_NAME"
  project = var.project_id
}

resource "google_sql_database_instance" "main" {
  # Password accessed via: data.google_secret_manager_secret_version.db_password.secret_data
  # ... other configuration
}
```

**Pattern 3: HashiCorp Vault (Provider-Agnostic)**

> **Note:** This example uses `vault_generic_secret` which works with both KV v1 and KV v2 secrets engines. For KV v2, include `/data/` in the path (e.g., `secret/data/database`). The data is accessed via `.data["key"]` regardless of KV version.

```hcl
data "vault_generic_secret" "db_creds" {
  # Path MUST be customized for your Vault secret location.
  path = "REPLACE_ME_VAULT_SECRET_PATH"
}

# AWS Example
resource "aws_db_instance" "main" {
  username = data.vault_generic_secret.db_creds.data["username"]
  password = data.vault_generic_secret.db_creds.data["password"]
}

# Azure Example
resource "azurerm_mssql_server" "main" {
  administrator_login          = data.vault_generic_secret.db_creds.data["username"]
  administrator_login_password = data.vault_generic_secret.db_creds.data["password"]
  # ... other configuration
}

# GCP Example
resource "google_sql_user" "main" {
  name     = data.vault_generic_secret.db_creds.data["username"]
  password = data.vault_generic_secret.db_creds.data["password"]
  instance = google_sql_database_instance.main.name
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

#### Backend Security Configuration

**AWS Example:**

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

**Azure Example:**

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "REPLACE_ME_RESOURCE_GROUP"
    storage_account_name = "REPLACE_ME_STORAGE_ACCOUNT"
    container_name       = "REPLACE_ME_CONTAINER"
    key                  = "prod/terraform.tfstate"
    # Encryption and locking are enabled by default on Azure Storage
    # Use managed identity or service principal for authentication
  }
}
```

**GCP Example:**

```hcl
terraform {
  backend "gcs" {
    bucket = "REPLACE_ME_STATE_BUCKET"
    prefix = "prod"
    # Encryption and locking are enabled by default on GCS
    # Use service account for authentication
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

**AWS Example - Specific permissions (GOOD):**

```hcl
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
```

**AWS Example - Overly permissive (BAD):**

```hcl
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

**Azure Example - Specific permissions (GOOD):**

```hcl
resource "azurerm_role_assignment" "storage_reader" {
  scope                = azurerm_storage_account.data.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}
```

**Azure Example - Overly permissive (BAD):**

```hcl
resource "azurerm_role_assignment" "bad_example" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Contributor"  # TOO BROAD - grants write access to entire subscription
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}
```

**GCP Example - Specific permissions (GOOD):**

```hcl
resource "google_storage_bucket_iam_member" "viewer" {
  bucket = google_storage_bucket.data.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.app.email}"
}
```

**GCP Example - Overly permissive (BAD):**

```hcl
resource "google_project_iam_member" "bad_example" {
  project = var.project_id
  role    = "roles/editor"  # TOO BROAD - grants write access to entire project
  member  = "serviceAccount:${google_service_account.app.email}"
}
```

### Sensitive Values in Meta-Arguments

Values used in `for_each` keys and `count` expressions appear in Terraform state and plan output, even if the source variable is marked `sensitive = true`. This creates a security risk where sensitive data can be exposed.

**Security requirements:**

- Sensitive values **MUST NOT** be used as `for_each` keys
- Sensitive values **MUST NOT** be used in `count` conditions where the value itself is exposed
- Use non-sensitive identifiers as keys and reference sensitive values only in resource attributes

**Anti-pattern (sensitive values exposed in state):**

```hcl
# BAD: Sensitive value used as for_each key - names will appear in state
variable "secret_names" {
  type      = list(string)
  sensitive = true
}

resource "aws_secretsmanager_secret" "secrets" {
  for_each = toset(var.secret_names)  # Keys leak to state!
  name     = each.key
}
```

**Correct pattern (non-sensitive keys):**

```hcl
# GOOD: Use non-sensitive identifiers as keys
variable "secrets" {
  type = map(object({
    name  = string
    value = string
  }))
  sensitive = true
}

resource "aws_secretsmanager_secret" "secrets" {
  for_each = { for k, v in var.secrets : k => v.name }
  name     = each.value  # each.key is the non-sensitive identifier
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

> **Note:** The `mock_provider` block requires Terraform 1.7.0 or later. For earlier versions of the test framework (Terraform 1.6.x), tests must use real provider credentials or skip provider-dependent tests.

**AWS Example:**

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

**Azure Example:**

```hcl
# tests/unit.tftest.hcl

mock_provider "azurerm" {
  mock_data "azurerm_client_config" {
    defaults = {
      tenant_id       = "00000000-0000-0000-0000-000000000000"
      subscription_id = "00000000-0000-0000-0000-000000000000"
    }
  }
}

run "resource_group_has_correct_location" {
  command = plan

  assert {
    condition     = azurerm_resource_group.main.location == "eastus"
    error_message = "Resource group should be in eastus"
  }
}
```

**GCP Example:**

```hcl
# tests/unit.tftest.hcl

mock_provider "google" {
  mock_data "google_compute_zones" {
    defaults = {
      names = ["us-central1-a", "us-central1-b", "us-central1-c"]
    }
  }
}

run "uses_all_compute_zones" {
  command = plan

  assert {
    condition     = length(google_compute_instance.main) == 3
    error_message = "Should create instance in each zone"
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

### TFLint Configuration

This repository's TFLint configuration is defined in `.tflint.hcl` at the repository root. The configuration:

- Enables the `terraform` plugin with the `recommended` preset
- Enforces `snake_case` naming conventions
- Requires documentation for variables and outputs
- Requires type declarations for variables
- Includes commented provider-specific plugins (AWS, Azure, GCP) that **SHOULD** be uncommented based on your cloud provider

When adopting this template, review and customize `.tflint.hcl` for your project's provider requirements.

> **Note:** When enabling provider-specific TFLint plugins (AWS, Azure, GCP), verify that you are using the latest stable versions. The plugin versions in the template may become outdated. Check the [TFLint Ruleset Registry](https://github.com/terraform-linters) for current versions.

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

## Related Documentation

For detailed implementation guidance beyond this instruction file, see the companion documents in `docs/terraform/`:

| Document | Purpose |
| --- | --- |
| [Terraform Linting Guide](../../docs/terraform/TERRAFORM_LINTING_GUIDE.md) | Detailed guidance on CI linting setup, TFLint configuration, and security scanning |
| [Terraform Testing Guide](../../docs/terraform/TERRAFORM_TESTING_GUIDE.md) | Comprehensive guide to Terraform test framework, test patterns, and CI integration |
| [Terraform Copilot Instructions Guide](../../docs/terraform/TERRAFORM_COPILOT_INSTRUCTIONS_GUIDE.md) | Design rationale and structure guidance for this instruction file |

These documents provide in-depth coverage of topics summarized in this instruction file.

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
