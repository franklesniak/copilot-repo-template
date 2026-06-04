function ConvertTo-GitHubAnnotationField {
    # .SYNOPSIS
    # Escapes a value for use in a GitHub Actions annotation field.
    #
    # .DESCRIPTION
    # Converts a value to a string and applies GitHub Actions workflow command
    # escaping for annotation field values. Field values require the common
    # command escaping plus colon and comma escaping because those characters
    # delimit annotation metadata.
    #
    # .PARAMETER Value
    # The value to escape. Null values are emitted as an empty string.
    #
    # .EXAMPLE
    # ConvertTo-GitHubAnnotationField -Value 'C:\src\script.ps1'
    # # Returns C%3A\src\script.ps1
    #
    # .INPUTS
    # None. This function does not accept pipeline input.
    #
    # .OUTPUTS
    # [string] The escaped annotation field value.
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
    [OutputType([string])]
    param(
        [AllowNull()]
        [object]$Value
    )

    Set-StrictMode -Version Latest

    if ($null -eq $Value) {
        return ''
    }

    $strEscapedValue = [string]$Value
    $strEscapedValue = $strEscapedValue.Replace('%', '%25')
    $strEscapedValue = $strEscapedValue.Replace("`r", '%0D')
    $strEscapedValue = $strEscapedValue.Replace("`n", '%0A')
    $strEscapedValue = $strEscapedValue.Replace(':', '%3A')
    $strEscapedValue = $strEscapedValue.Replace(',', '%2C')

    return $strEscapedValue
}

function ConvertTo-GitHubAnnotationMessage {
    # .SYNOPSIS
    # Escapes a value for use as a GitHub Actions annotation message.
    #
    # .DESCRIPTION
    # Converts a value to a string and applies GitHub Actions workflow command
    # escaping for annotation message values. Message values do not require the
    # additional colon or comma escaping used by annotation metadata fields.
    #
    # .PARAMETER Value
    # The value to escape. Null values are emitted as an empty string.
    #
    # .EXAMPLE
    # ConvertTo-GitHubAnnotationMessage -Value "Line 1`nLine 2"
    # # Returns Line 1%0ALine 2
    #
    # .INPUTS
    # None. This function does not accept pipeline input.
    #
    # .OUTPUTS
    # [string] The escaped annotation message.
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
    [OutputType([string])]
    param(
        [AllowNull()]
        [object]$Value
    )

    Set-StrictMode -Version Latest

    if ($null -eq $Value) {
        return ''
    }

    $strEscapedValue = [string]$Value
    $strEscapedValue = $strEscapedValue.Replace('%', '%25')
    $strEscapedValue = $strEscapedValue.Replace("`r", '%0D')
    $strEscapedValue = $strEscapedValue.Replace("`n", '%0A')

    return $strEscapedValue
}

function Get-PSScriptAnalyzerFindingProperty {
    # .SYNOPSIS
    # Reads a named property from a PSScriptAnalyzer finding.
    #
    # .DESCRIPTION
    # Safely retrieves a property from an analyzer finding object. Missing
    # properties and null findings return null so callers can treat malformed
    # synthetic or analyzer output as unknown-severity findings.
    #
    # .PARAMETER Finding
    # The analyzer finding object to inspect.
    #
    # .PARAMETER Name
    # The property name to read from the finding.
    #
    # .EXAMPLE
    # Get-PSScriptAnalyzerFindingProperty -Finding $objFinding -Name 'Severity'
    # # Returns the Severity property value when present.
    #
    # .INPUTS
    # None. This function does not accept pipeline input.
    #
    # .OUTPUTS
    # [object] The property value, or null when the property is absent.
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
    [OutputType([object])]
    param(
        [AllowNull()]
        [object]$Finding,

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$Name
    )

    Set-StrictMode -Version Latest

    if ($null -eq $Finding) {
        return $null
    }

    $objProperty = $Finding.PSObject.Properties[$Name]
    if ($null -eq $objProperty) {
        return $null
    }

    return $objProperty.Value
}

function ConvertTo-PSScriptAnalyzerPositiveInteger {
    # .SYNOPSIS
    # Converts a value to a positive integer for annotation metadata.
    #
    # .DESCRIPTION
    # Converts line and column values from analyzer findings to positive
    # integers. Missing, non-numeric, zero, and negative values return 0 so the
    # caller can omit invalid annotation metadata.
    #
    # .PARAMETER Value
    # The value to parse as a positive integer.
    #
    # .EXAMPLE
    # ConvertTo-PSScriptAnalyzerPositiveInteger -Value '12'
    # # Returns 12
    #
    # .INPUTS
    # None. This function does not accept pipeline input.
    #
    # .OUTPUTS
    # [int] A positive integer, or 0 when the value is not a positive integer.
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
    [OutputType([int])]
    param(
        [AllowNull()]
        [object]$Value
    )

    Set-StrictMode -Version Latest

    $intParsedValue = 0
    if ($null -eq $Value) {
        return $intParsedValue
    }

    [void]([int]::TryParse(([string]$Value), [ref]$intParsedValue))
    if ($intParsedValue -lt 1) {
        return 0
    }

    return $intParsedValue
}

function ConvertTo-RepositoryRelativePath {
    # .SYNOPSIS
    # Converts an absolute path to a repository-relative path.
    #
    # .DESCRIPTION
    # When a repository root is provided and the path is located beneath it, the
    # leading root prefix is removed so GitHub Actions annotations reference a
    # repository-relative file. Paths that are empty, lack a root, or fall
    # outside the root are returned unchanged. Backslashes are normalized to
    # forward slashes for the prefix comparison and in the repository-relative
    # result; a path returned unchanged keeps its original separators.
    #
    # .PARAMETER Path
    # The path to convert. A null path is returned as an empty string;
    # an empty or whitespace-only path is returned unchanged.
    #
    # .PARAMETER RepositoryRoot
    # The repository root to make the path relative to. Null and empty roots
    # leave the path unchanged.
    #
    # .EXAMPLE
    # ConvertTo-RepositoryRelativePath -Path '/runner/repo/src/a.ps1' -RepositoryRoot '/runner/repo'
    # # Returns src/a.ps1
    #
    # .INPUTS
    # None. This function does not accept pipeline input.
    #
    # .OUTPUTS
    # [string] The repository-relative path, or the original path when it cannot
    # be made relative.
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
    [OutputType([string])]
    param(
        [AllowNull()]
        [object]$Path,

        [AllowNull()]
        [AllowEmptyString()]
        [string]$RepositoryRoot
    )

    Set-StrictMode -Version Latest

    if ($null -eq $Path) {
        return ''
    }

    $strPath = [string]$Path
    if ([string]::IsNullOrWhiteSpace($strPath)) {
        return $strPath
    }
    if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
        return $strPath
    }

    $strNormalizedPath = $strPath.Replace('\', '/')
    $strNormalizedRoot = $RepositoryRoot.Replace('\', '/').TrimEnd('/')
    if ($strNormalizedRoot.Length -eq 0) {
        return $strPath
    }

    $strRootPrefix = $strNormalizedRoot + '/'
    if ($strNormalizedPath.StartsWith($strRootPrefix, [System.StringComparison]::Ordinal)) {
        return $strNormalizedPath.Substring($strRootPrefix.Length)
    }

    return $strPath
}

function Resolve-PSScriptAnalyzerGate {
    # .SYNOPSIS
    # Resolves PSScriptAnalyzer findings into a CI gate decision.
    #
    # .DESCRIPTION
    # Resolves a configured PSScriptAnalyzer gate mode and evaluates analyzer
    # findings by severity. Strict mode fails Error, Warning, and unknown
    # severity findings. First-adoption mode fails Error and unknown severity
    # findings while annotating Warning and Information findings as tracked
    # adoption debt. Information findings are annotation-only in both modes.
    #
    # Missing, empty, and unrecognized mode values resolve to strict mode.
    # The returned object includes deterministic summary data, GitHub Actions
    # annotation commands for every finding, normalized finding records, and the
    # final gate decision.
    #
    # .PARAMETER Mode
    # The requested gate mode. Supported values are strict and first-adoption.
    #
    # .PARAMETER AnalyzerFinding
    # The PSScriptAnalyzer findings to evaluate.
    #
    # .PARAMETER RepositoryRoot
    # Optional repository root used to render annotation file paths relative to
    # the repository. Defaults to the GITHUB_WORKSPACE environment variable so
    # GitHub Actions annotations link to the correct file.
    #
    # .EXAMPLE
    # $objGate = Resolve-PSScriptAnalyzerGate -Mode 'first-adoption' -AnalyzerFinding $arrFinding
    # if ($objGate.ShouldFail) {
    #     exit 1
    # }
    #
    # .INPUTS
    # None. This function does not accept pipeline input.
    #
    # .OUTPUTS
    # [pscustomobject] Gate result with Mode, ShouldFail, Summary,
    # SummaryLines, AnnotationCommands, and Findings properties.
    #
    # .NOTES
    # Version: 1.0.20260604.0
    # Positional parameters are not supported.
    #
    [CmdletBinding(PositionalBinding = $false)]
    [OutputType([pscustomobject])]
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Mode,

        [AllowNull()]
        [object[]]$AnalyzerFinding,

        [AllowNull()]
        [AllowEmptyString()]
        [string]$RepositoryRoot = $env:GITHUB_WORKSPACE
    )

    Set-StrictMode -Version Latest

    $strRequestedMode = ''
    if ($null -ne $Mode) {
        $strRequestedMode = $Mode.Trim().ToLowerInvariant()
    }

    $strResolvedMode = 'strict'
    if ($strRequestedMode -eq 'first-adoption') {
        $strResolvedMode = 'first-adoption'
    }

    $arrAnalyzerFinding = @()
    if ($null -ne $AnalyzerFinding) {
        $arrAnalyzerFinding = @($AnalyzerFinding)
    }

    $listNormalizedFinding = [System.Collections.Generic.List[pscustomobject]]::new()
    $listAnnotationCommand = [System.Collections.Generic.List[string]]::new()

    $intErrorCount = 0
    $intWarningCount = 0
    $intInformationCount = 0
    $intUnknownSeverityCount = 0
    $intBlockingCount = 0
    $intDebtCount = 0

    foreach ($objFinding in $arrAnalyzerFinding) {
        $objSeverityValue = Get-PSScriptAnalyzerFindingProperty -Finding $objFinding -Name 'Severity'
        $strOriginalSeverity = ''
        if ($null -ne $objSeverityValue) {
            $strOriginalSeverity = ([string]$objSeverityValue).Trim()
        }

        $strNormalizedSeverity = 'Unknown'
        switch ($strOriginalSeverity.ToLowerInvariant()) {
            'error' {
                $strNormalizedSeverity = 'Error'
                $intErrorCount++
                break
            }
            'warning' {
                $strNormalizedSeverity = 'Warning'
                $intWarningCount++
                break
            }
            'information' {
                $strNormalizedSeverity = 'Information'
                $intInformationCount++
                break
            }
            default {
                $intUnknownSeverityCount++
                break
            }
        }

        $boolFailsGate = $false
        if ($strNormalizedSeverity -eq 'Error') {
            $boolFailsGate = $true
        } elseif ($strNormalizedSeverity -eq 'Warning') {
            $boolFailsGate = ($strResolvedMode -eq 'strict')
        } elseif ($strNormalizedSeverity -eq 'Unknown') {
            $boolFailsGate = $true
        }

        $boolTrackedDebt = (
            ($strResolvedMode -eq 'first-adoption') -and
            (-not $boolFailsGate) -and
            (($strNormalizedSeverity -eq 'Warning') -or ($strNormalizedSeverity -eq 'Information'))
        )

        if ($boolFailsGate) {
            $intBlockingCount++
        }

        if ($boolTrackedDebt) {
            $intDebtCount++
        }

        $strAnnotationLevel = 'notice'
        if (($strNormalizedSeverity -eq 'Error') -or ($strNormalizedSeverity -eq 'Unknown')) {
            $strAnnotationLevel = 'error'
        } elseif ($strNormalizedSeverity -eq 'Warning') {
            $strAnnotationLevel = 'warning'
        }

        $strRuleName = [string](Get-PSScriptAnalyzerFindingProperty -Finding $objFinding -Name 'RuleName')
        if ([string]::IsNullOrWhiteSpace($strRuleName)) {
            $strRuleName = 'PSScriptAnalyzer'
        }

        $strMessage = [string](Get-PSScriptAnalyzerFindingProperty -Finding $objFinding -Name 'Message')
        if ([string]::IsNullOrWhiteSpace($strMessage)) {
            $strMessage = 'PSScriptAnalyzer finding did not include a message.'
        }

        $strScriptPath = [string](Get-PSScriptAnalyzerFindingProperty -Finding $objFinding -Name 'ScriptPath')
        if ([string]::IsNullOrWhiteSpace($strScriptPath)) {
            $strScriptPath = [string](Get-PSScriptAnalyzerFindingProperty -Finding $objFinding -Name 'FileName')
        }
        $strScriptPath = ConvertTo-RepositoryRelativePath -Path $strScriptPath -RepositoryRoot $RepositoryRoot

        $intLine = ConvertTo-PSScriptAnalyzerPositiveInteger -Value (
            Get-PSScriptAnalyzerFindingProperty -Finding $objFinding -Name 'Line'
        )
        $intColumn = ConvertTo-PSScriptAnalyzerPositiveInteger -Value (
            Get-PSScriptAnalyzerFindingProperty -Finding $objFinding -Name 'Column'
        )

        $strDisplaySeverity = $strNormalizedSeverity
        if (($strNormalizedSeverity -eq 'Unknown') -and (-not [string]::IsNullOrWhiteSpace($strOriginalSeverity))) {
            $strDisplaySeverity = "Unknown ($strOriginalSeverity)"
        }

        $strAnnotationMessage = '[{0}] {1} - {2}' -f $strDisplaySeverity, $strRuleName, $strMessage

        $listAnnotationField = [System.Collections.Generic.List[string]]::new()
        if (-not [string]::IsNullOrWhiteSpace($strScriptPath)) {
            $listAnnotationField.Add(('file={0}' -f (ConvertTo-GitHubAnnotationField -Value $strScriptPath)))
        }
        if ($intLine -gt 0) {
            $listAnnotationField.Add(('line={0}' -f $intLine))
        }
        if ($intColumn -gt 0) {
            $listAnnotationField.Add(('col={0}' -f $intColumn))
        }

        $strEscapedAnnotationMessage = ConvertTo-GitHubAnnotationMessage -Value $strAnnotationMessage
        if ($listAnnotationField.Count -gt 0) {
            $strAnnotationField = $listAnnotationField.ToArray() -join ','
            $listAnnotationCommand.Add(('::{0} {1}::{2}' -f $strAnnotationLevel, $strAnnotationField, $strEscapedAnnotationMessage))
        } else {
            $listAnnotationCommand.Add(('::{0}::{1}' -f $strAnnotationLevel, $strEscapedAnnotationMessage))
        }

        $listNormalizedFinding.Add(
            [pscustomobject]@{
                Severity = $strNormalizedSeverity
                OriginalSeverity = $strOriginalSeverity
                RuleName = $strRuleName
                Message = $strMessage
                ScriptPath = $strScriptPath
                Line = $intLine
                Column = $intColumn
                AnnotationLevel = $strAnnotationLevel
                FailsGate = $boolFailsGate
                TrackedDebt = $boolTrackedDebt
            }
        )
    }

    $intTotalCount = $listNormalizedFinding.Count
    $boolShouldFail = ($intBlockingCount -gt 0)

    $objSummary = [pscustomobject]@{
        TotalCount = $intTotalCount
        ErrorCount = $intErrorCount
        WarningCount = $intWarningCount
        InformationCount = $intInformationCount
        UnknownSeverityCount = $intUnknownSeverityCount
        BlockingCount = $intBlockingCount
        DebtCount = $intDebtCount
    }

    $listSummaryLine = [System.Collections.Generic.List[string]]::new()
    $listSummaryLine.Add(('PSScriptAnalyzer gate mode: {0}.' -f $strResolvedMode))

    if ($intTotalCount -eq 0) {
        $listSummaryLine.Add('No PSScriptAnalyzer findings were reported.')
        $listSummaryLine.Add('Result: pass.')
    } else {
        $strFindingSummary = 'Findings: {0} total; {1} Error; {2} Warning; {3} Information; {4} unknown severity.' -f $intTotalCount, $intErrorCount, $intWarningCount, $intInformationCount, $intUnknownSeverityCount
        $listSummaryLine.Add($strFindingSummary)

        if ($strResolvedMode -eq 'first-adoption') {
            if ($intDebtCount -gt 0) {
                $strWarningDebtSummary = 'Warning debt: {0} Warning and {1} Information finding(s) are annotated as tracked debt.' -f $intWarningCount, $intInformationCount
                $listSummaryLine.Add($strWarningDebtSummary)
                $listSummaryLine.Add(
                    'Record warning debt in _TODO-repo-init.md or a post-adoption issue, then return PSSCRIPTANALYZER_GATE_MODE to strict after the debt is remediated.'
                )
            } else {
                $listSummaryLine.Add('Warning debt: none.')
            }

            if ($boolShouldFail) {
                $listSummaryLine.Add('Result: fail because Error or unknown-severity findings are present.')
            } else {
                $listSummaryLine.Add('Result: pass; Warning and Information findings were annotated without failing first-adoption mode.')
            }
        } else {
            $listSummaryLine.Add('Strict gate: Error, Warning, and unknown-severity findings fail CI; Information findings are annotation-only.')
            if ($boolShouldFail) {
                $listSummaryLine.Add('Result: fail because blocking findings are present.')
            } else {
                $listSummaryLine.Add('Result: pass.')
            }
        }
    }

    return [pscustomobject]@{
        Mode = $strResolvedMode
        ShouldFail = $boolShouldFail
        Summary = $objSummary
        SummaryLines = [string[]]$listSummaryLine.ToArray()
        AnnotationCommands = [string[]]$listAnnotationCommand.ToArray()
        Findings = [object[]]$listNormalizedFinding.ToArray()
    }
}
