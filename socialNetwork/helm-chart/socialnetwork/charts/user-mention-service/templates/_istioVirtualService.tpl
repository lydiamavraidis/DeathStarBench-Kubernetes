{{- define "socialnetwork.templates.istioVirtualService" }}
{{- if and .Values.istio .Values.istio.enabled }}
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: {{ .Values.name }}
  namespace: {{ $.Release.Namespace }}
  labels:
    app: {{ .Values.name }}
spec:
  hosts:
  - {{ .Values.name }}
  - {{ .Values.name }}.{{ $.Release.Namespace }}
  - {{ .Values.name }}.{{ $.Release.Namespace }}.svc.cluster.local
  http:
  - route:
    - destination:
        host: {{ .Values.name }}
        port:
          number: 9090
        subset: "all"
    timeout: {{ .Values.istio.virtualService.timeout }}
    retries:
      attempts: {{ .Values.istio.virtualService.retries.attempts }}
      perTryTimeout: {{ .Values.istio.virtualService.retries.perTryTimeout }}
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: {{ .Values.name }}
  namespace: {{ $.Release.Namespace }}
  labels:
    app: {{ .Values.name }}
spec:
  host: {{ .Values.name }}
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        maxRequestsPerConnection: 2
        h2UpgradePolicy: UPGRADE
    loadBalancer:
      simple: {{ .Values.istio.virtualService.loadBalancing }}
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
  {{- range $vmId, $vmConfig := .Values.deployments }}
  {{- if $vmConfig.enabled }}
  - name: {{ $vmId }}
    labels:
      vm: {{ $vmId }}
  {{- end }}
  {{- end }}
  - name: "all"
    labels: {}
{{- end }}
{{- end }}