BeforeAll {
    $strRepositoryRoot = Split-Path -Path (Split-Path -Path $PSScriptRoot -Parent) -Parent
    . (Join-Path -Path $strRepositoryRoot -ChildPath 'src/tools/Resolve-PSScriptAnalyzerGate.ps1')

    function Get-SyntheticAnalyzerFinding {
        # .SYNOPSIS
        # Creates a synthetic PSScriptAnalyzer finding for tests.
        #
        # .DESCRIPTION
        # Builds a PSCustomObject that contains the analyzer fields used by
        # Resolve-PSScriptAnalyzerGate. Tests use synthetic findings so they can
        # exercise Information and unknown severities without changing the
        # committed PSScriptAnalyzer settings.
        #
        # .PARAMETER Severity
        # The severity value to include in the finding.
        #
        # .PARAMETER RuleName
        # The rule name to include in the finding.
        #
        # .PARAMETER Message
        # The message to include in the finding.
        #
        # .PARAMETER ScriptPath
        # The script path to include in the finding.
        #
        # .PARAMETER Line
        # The line number to include in the finding.
        #
        # .PARAMETER Column
        # The column number to include in the finding.
        #
        # .EXAMPLE
        # Get-SyntheticAnalyzerFinding -Severity 'Warning'
        # # Returns a synthetic Warning finding.
        #
        # .INPUTS
        # None. This function does not accept pipeline input.
        #
        # .OUTPUTS
        # [pscustomobject] A synthetic analyzer finding.
        #
        # .NOTES
        # PRIVATE/INTERNAL HELPER - This function is not part of the public
        # API surface. Parameters, return shape, and positional contract may
        # change without notice.
        #
        # Version: 1.0.20260604.0
        # Positional parameters are not supported.
        #
        [CmdletBinding(PositionalBinding = $false)]
        [OutputType([pscustomobject])]
        param(
            [AllowNull()]
            [object]$Severity = 'Warning',

            [ValidateNotNullOrEmpty()]
            [string]$RuleName = 'PSExampleRule',

            [ValidateNotNullOrEmpty()]
            [string]$Message = 'Synthetic analyzer finding.',

            [ValidateNotNullOrEmpty()]
            [string]$ScriptPath = 'src/tools/TestScript.ps1',

            [int]$Line = 5,

            [int]$Column = 9
        )

        Set-StrictMode -Version Latest

        return [pscustomobject]@{
            Severity = $Severity
            RuleName = $RuleName
            Message = $Message
            ScriptPath = $ScriptPath
            Line = $Line
            Column = $Column
        }
    }
}

Describe "Resolve-PSScriptAnalyzerGate" {
    Context "When resolving gate modes" {
        It "Resolves a missing mode to strict" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Information'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.Mode | Should -Be 'strict'
        }

        It "Resolves an empty mode to strict" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Information'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode '' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.Mode | Should -Be 'strict'
        }

        It "Resolves an unrecognized mode to strict" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Information'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'relaxed' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.Mode | Should -Be 'strict'
        }

        It "Resolves first-adoption mode when explicitly configured" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Information'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'first-adoption' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.Mode | Should -Be 'first-adoption'
        }
    }

    Context "When strict mode gates severities" {
        It "Fails Error findings" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Error'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'strict' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.ShouldFail | Should -BeTrue
            $objResult.Summary.BlockingCount | Should -Be 1
        }

        It "Fails Warning findings" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Warning'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'strict' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.ShouldFail | Should -BeTrue
            $objResult.Summary.BlockingCount | Should -Be 1
        }

        It "Allows Information findings" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Information'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'strict' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.ShouldFail | Should -BeFalse
            $objResult.Summary.BlockingCount | Should -Be 0
        }

        It "Fails unknown-severity findings" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Audit'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'strict' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.ShouldFail | Should -BeTrue
            $objResult.Summary.UnknownSeverityCount | Should -Be 1
        }
    }

    Context "When first-adoption mode gates severities" {
        It "Fails Error findings" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Error'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'first-adoption' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.ShouldFail | Should -BeTrue
            $objResult.Summary.BlockingCount | Should -Be 1
        }

        It "Allows Warning findings as tracked debt" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Warning'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'first-adoption' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.ShouldFail | Should -BeFalse
            $objResult.Summary.BlockingCount | Should -Be 0
            $objResult.Summary.DebtCount | Should -Be 1
            $objResult.Findings.Count | Should -Be 1
            $objResult.Findings[0].TrackedDebt | Should -BeTrue
        }

        It "Allows Information findings as tracked debt" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Information'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'first-adoption' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.ShouldFail | Should -BeFalse
            $objResult.Summary.BlockingCount | Should -Be 0
            $objResult.Summary.DebtCount | Should -Be 1
            $objResult.Findings.Count | Should -Be 1
            $objResult.Findings[0].TrackedDebt | Should -BeTrue
        }

        It "Fails unknown-severity findings" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Audit'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'first-adoption' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.ShouldFail | Should -BeTrue
            $objResult.Summary.UnknownSeverityCount | Should -Be 1
        }
    }

    Context "When findings cannot be parsed normally" {
        It "Treats a missing severity as unknown in strict mode" {
            # Arrange
            $objFinding = [pscustomobject]@{
                RuleName = 'PSMissingSeverity'
                Message = 'Missing severity.'
                ScriptPath = 'src/tools/TestScript.ps1'
                Line = 3
                Column = 7
            }

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'strict' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.ShouldFail | Should -BeTrue
            $objResult.Findings.Count | Should -Be 1
            $objResult.Findings[0].Severity | Should -Be 'Unknown'
        }

        It "Treats a missing severity as unknown in first-adoption mode" {
            # Arrange
            $objFinding = [pscustomobject]@{
                RuleName = 'PSMissingSeverity'
                Message = 'Missing severity.'
                ScriptPath = 'src/tools/TestScript.ps1'
                Line = 3
                Column = 7
            }

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'first-adoption' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.ShouldFail | Should -BeTrue
            $objResult.Findings.Count | Should -Be 1
            $objResult.Findings[0].Severity | Should -Be 'Unknown'
        }
    }

    Context "When building annotations and summaries" {
        It "Creates one annotation command for every finding" {
            # Arrange
            $arrFinding = @(
                Get-SyntheticAnalyzerFinding -Severity 'Error'
                Get-SyntheticAnalyzerFinding -Severity 'Warning'
                Get-SyntheticAnalyzerFinding -Severity 'Information'
                Get-SyntheticAnalyzerFinding -Severity 'Audit'
            )

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'first-adoption' -AnalyzerFinding $arrFinding

            # Assert
            $objResult.AnnotationCommands | Should -HaveCount 4
            $objResult.AnnotationCommands[0] | Should -Match '^::error '
            $objResult.AnnotationCommands[1] | Should -Match '^::warning '
            $objResult.AnnotationCommands[2] | Should -Match '^::notice '
            $objResult.AnnotationCommands[3] | Should -Match '^::error '
        }

        It "Prints a first-adoption warning debt summary with Information counts" {
            # Arrange
            $arrFinding = @(
                Get-SyntheticAnalyzerFinding -Severity 'Warning'
                Get-SyntheticAnalyzerFinding -Severity 'Warning'
                Get-SyntheticAnalyzerFinding -Severity 'Information'
            )

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'first-adoption' -AnalyzerFinding $arrFinding

            # Assert
            $objResult.ShouldFail | Should -BeFalse
            $objResult.Summary.DebtCount | Should -Be 3
            ($objResult.SummaryLines -join "`n") | Should -Match 'Warning debt: 2 Warning and 1 Information'
            ($objResult.SummaryLines -join "`n") | Should -Match '_TODO-repo-init\.md or a post-adoption issue'
        }

        It "Prints a strict summary that identifies blocking findings" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Warning'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'strict' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.ShouldFail | Should -BeTrue
            ($objResult.SummaryLines -join "`n") | Should -Match 'Strict gate'
            ($objResult.SummaryLines -join "`n") | Should -Match 'Result: fail'
        }
    }

    Context "When normalizing annotation paths" {
        It "Makes an absolute ScriptPath relative to the repository root" {
            # Arrange
            $strRepositoryRoot = '/home/runner/work/repo/repo'
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Warning' -ScriptPath "$strRepositoryRoot/src/tools/Demo.ps1"

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'strict' -RepositoryRoot $strRepositoryRoot -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.Findings.Count | Should -Be 1
            $objResult.Findings[0].ScriptPath | Should -Be 'src/tools/Demo.ps1'
            ($objResult.AnnotationCommands -join "`n") | Should -Match 'file=src/tools/Demo\.ps1'
        }

        It "Leaves a ScriptPath unchanged when it is outside the repository root" {
            # Arrange
            $objFinding = Get-SyntheticAnalyzerFinding -Severity 'Warning' -ScriptPath '/var/other/Demo.ps1'

            # Act
            $objResult = Resolve-PSScriptAnalyzerGate -Mode 'strict' -RepositoryRoot '/home/runner/work/repo/repo' -AnalyzerFinding @($objFinding)

            # Assert
            $objResult.Findings.Count | Should -Be 1
            $objResult.Findings[0].ScriptPath | Should -Be '/var/other/Demo.ps1'
        }
    }
}
