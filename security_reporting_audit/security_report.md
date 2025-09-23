<h2 style='font-size: 20px; margin-top: 25px; margin-bottom: 8px;'>Executive Summary</h2>
<p style='font-size: 15px; margin-top: 0; margin-bottom: 15px;'>This section provides a high-level overview of identified risks with a focus on business impact.</p>
<table border="1" cellspacing="0" cellpadding="6" width="90%">
<tr><th>Description</th><th>Business Impact</th></tr>
<tr><td>Unpatched VPN gateway</td><td>High</td></tr>
<tr><td>Weak password policy</td><td>Medium</td></tr>
</table>

<h2 style='font-size: 20px; margin-top: 25px; margin-bottom: 8px;'>Technical Details</h2>
<p style='font-size: 15px; margin-top: 0; margin-bottom: 15px;'>Detailed findings with anonymized evidence and mapped compliance controls:</p>
<table border="1" cellspacing="0" cellpadding="6" width="100%">
<tr><th>ID</th><th>Evidence</th><th>Risk</th><th>Mapped Compliance</th></tr>
<tr><td>F001</td><td>user@domain.local (anonymized)</td><td>High</td><td>ISO 27001: A.9.2.1</td></tr>
<tr><td>F002</td><td>Firewall rule ANY→ANY</td><td>Critical</td><td>NIST CSF: PR.AC-1, PR.AC-5</td></tr>
</table>

<h2 style='font-size: 20px; margin-top: 25px; margin-bottom: 8px;'>Remediation Roadmap</h2>
<p style='font-size: 15px; margin-top: 0; margin-bottom: 15px;'>Prioritized actions with guidance:</p>
<table border="1" cellspacing="0" cellpadding="6" width="100%">
<tr><th>Priority</th><th>Action</th><th>Implementation Guidance</th></tr>
<tr><td>1</td><td>Patch VPN firmware</td><td>Apply the latest vendor firmware update for your VPN device.</td></tr>
<tr><td>2</td><td>Implement strong password policy</td><td>Configure minimum 12-character complex passwords and enforce rotation policies.</td></tr>
</table>

<h2 style='font-size: 20px; margin-top: 25px; margin-bottom: 8px;'>Compliance Report</h2>
<p style='font-size: 15px; margin-top: 0; margin-bottom: 15px;'>Mapping to relevant standards:</p>
<table border="1" cellspacing="0" cellpadding="6" width="80%">
<tr><th>Standard</th><th>Mapping</th></tr>
<tr><td>NIST CSF</td><td>PR.AC-1, PR.AC-5</td></tr>
<tr><td>ISO 27001</td><td>A.9.2.1 User Access Management</td></tr>
</table>

<h2 style='text-align: center; font-size: 20px; margin-top: 30px; margin-bottom: 10px;'>Audit Trail</h2>
### Process Logging

- Steps performed during anonymization and analysis were logged.

### Transformation Mapping

- Encrypted mapping token (store separately for authorized retrieval): `gAAAAABo0oHv0ZiFTKGQduoYyHYPW2povkl38UP906-pHtDWuQ7dNxOW-rex5gDrdPYaghkMJZBhrQ4HldqtZnjwuyOvZDh5zLpL4NuX302Dy-PEWJg4UuTFzzXfQRWhg-SPyWhfmM8rjb9LUn-Vd_Ome7u8p0Fq6w==`

### Decision Rationale

- Certain findings were emphasized due to business impact (e.g., ANY→ANY firewall rule flagged as Critical).

### Quality Metrics

<table border="1" cellspacing="0" cellpadding="5" width="60%">
<tr><th align='left'>Metric</th><th align='center'>Value</th></tr>
<tr><td>anonymization_coverage</td><td align='center'>0.95</td></tr>
<tr><td>reidentification_risk</td><td align='center'>0.02</td></tr>
<tr><td>analysis_accuracy</td><td align='center'>0.9</td></tr>
</table>

<h2 style='text-align: center; font-size: 20px; margin-top: 30px; margin-bottom: 10px;'>Appendices</h2>
<h2 style='text-align: center; margin-top: 30px; margin-bottom: 15px;'></h2>
#### Audit Log Extract (first entries)

- `{"ts": "2025-09-20 12:48:16", "component": "anonymizer", "event_type": "mapping_created", "details": {"entity": "user@domain.com", "token": "user_xxx"}}`

- `{"ts": "2025-09-20 12:48:16", "component": "analysis", "event_type": "finding_added", "details": {"id": "F002", "desc": "Firewall rule ANY\u2192ANY"}}`

- `{"ts": "2025-09-20 12:55:30", "component": "anonymizer", "event_type": "mapping_created", "details": {"entity": "user@domain.com", "token": "user_xxx"}}`

- `{"ts": "2025-09-20 12:55:30", "component": "analysis", "event_type": "finding_added", "details": {"id": "F002", "desc": "Firewall rule ANY\u2192ANY"}}`

- `{"ts": "2025-09-20 12:55:36", "component": "anonymizer", "event_type": "mapping_created", "details": {"entity": "user@domain.com", "token": "user_xxx"}}`

## References

- NIST Cybersecurity Framework

- ISO 27001:2013 Security Controls
