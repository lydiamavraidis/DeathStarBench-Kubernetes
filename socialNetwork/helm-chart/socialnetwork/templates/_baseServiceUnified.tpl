{{- define "socialnetwork.templates.baseServiceUnified" }}
apiVersion: v1
kind: Service
metadata:
  name: {{ .Values.name }}
  namespace: {{ $.Release.Namespace }}
  labels:
    app: {{ .Values.name }}
    service: {{ .Values.name }}
spec:
  type: {{ .Values.type | default .Values.global.serviceType }}
  ports:  
  {{- range .Values.ports }}
  - name: "{{ .port }}"
    port: {{ .port }}
    {{- if .protocol}}
    protocol: {{ .protocol }}
    {{- end}}
    targetPort: {{ .targetPort }}
    {{- if eq (.port | toString) "9090" }}
    appProtocol: thrift
    {{- else }}
    appProtocol: grpc
    {{- end }}
  {{- end}}
  selector:
    service: {{ .Values.name }}
{{- end }}