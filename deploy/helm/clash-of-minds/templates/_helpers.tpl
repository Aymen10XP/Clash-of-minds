{{- define "clash.name" -}}
clash-of-minds
{{- end }}

{{- define "clash.labels" -}}
app.kubernetes.io/name: {{ include "clash.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
