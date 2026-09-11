{{- define "socialnetwork.templates.baseConfigMapVM" }}
{{- range $vmId, $vmConfig := .Values.deployments }}
{{- if $vmConfig.enabled }}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ $.Values.name }}-{{ $vmId }}
  namespace: {{ $.Release.Namespace }}
  labels:
    app: {{ $.Values.name }}
    vm: {{ $vmId }}
data:
  {{- range $configMap := $.Values.configMaps }}
  {{- $filePath := printf "configs/%s" $configMap.value }}
  {{ $configMap.name }}: |
{{ tpl ($.Files.Get $filePath) $ | indent 4 }}
  {{- end }}
{{- end }}
{{- end }}
{{- end }}

