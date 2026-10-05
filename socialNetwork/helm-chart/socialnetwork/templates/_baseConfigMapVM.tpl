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
  sidecar-prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    scrape_configs:
    - job_name: 'envoy-local'
      static_configs:
      - targets: ['localhost:15000']
      metrics_path: /stats/prometheus
{{- end }}
{{- end }}
{{- end }}
