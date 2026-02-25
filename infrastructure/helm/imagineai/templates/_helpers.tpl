{{/*
Expand the name of the chart.
*/}}
{{- define "imagineai.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "imagineai.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Create chart name and version for chart label.
*/}}
{{- define "imagineai.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "imagineai.labels" -}}
helm.sh/chart: {{ include "imagineai.chart" . }}
app.kubernetes.io/part-of: imagineai-platform
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
{{- end }}

{{/*
Selector labels for a component
*/}}
{{- define "imagineai.selectorLabels" -}}
app.kubernetes.io/name: {{ .component }}
app.kubernetes.io/instance: {{ include "imagineai.fullname" .root }}-{{ .component }}
{{- end }}

{{/*
Image reference helper
*/}}
{{- define "imagineai.image" -}}
{{- $registry := .root.Values.image.registry -}}
{{- $tag := default .root.Values.image.tag .imageTag -}}
{{- if $registry -}}
{{ $registry }}/{{ .repository }}:{{ $tag }}
{{- else -}}
{{ .repository }}:{{ $tag }}
{{- end -}}
{{- end }}

{{/*
Service account name
*/}}
{{- define "imagineai.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "imagineai.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
