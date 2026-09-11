{{- define "socialnetwork.templates.baseNginxDeploymentVM" }}
{{- range $vmId, $vmConfig := .Values.deployments }}
{{- if $vmConfig.enabled }}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    service: {{ $.Values.name }}
    vm: {{ $vmId }}
  name: {{ $.Values.name }}-{{ $vmId }}
  namespace: {{ $.Release.Namespace }}
spec: 
  replicas: {{ $vmConfig.replicas | default $.Values.global.replicas }}
  selector:
    matchLabels:
      service: {{ $.Values.name }}
      vm: {{ $vmId }}
  template:
    metadata:
      labels:
        service: {{ $.Values.name }}
        app: {{ $.Values.name }}
        vm: {{ $vmId }}
        version: v1
      annotations:
        sidecar.istio.io/inject: "true"
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                - {{ $vmConfig.nodeName }}
      containers:
      {{- with $.Values.container }}
      - name: "{{ .name }}"
        image: {{ .dockerRegistry | default $.Values.global.dockerRegistry }}/{{ .image }}:{{ .imageVersion | default $.Values.global.defaultImageVersion }}
        imagePullPolicy: {{ .imagePullPolicy | default $.Values.global.imagePullPolicy }}
        ports:
        {{- range $cport := .ports }}
        - containerPort: {{ $cport.containerPort }}
          name: {{ $cport.name | default "http" }}
        {{- end }} 
        {{- if .env }}
        env:
        {{- range $e := .env}}
        - name: {{ $e.name }}
          value: "{{ (tpl ($e.value | toString) $) }}"
        {{ end -}}
        {{ end -}}
        {{- if .command}}
        command: 
        - {{ .command }}
        {{- end -}}
        {{- if .args}}
        args:
        {{- range $arg := .args}}
        - {{ $arg }}
        {{- end -}}
        {{- end }}
        {{- if .resources }}  
        resources:
          {{ toYaml .resources | nindent 10 | trim }}
        {{- else if hasKey $.Values.global "resources" }}           
        resources:
          {{ toYaml $.Values.global.resources | nindent 10 | trim }}
        {{- end }}  
        {{- if $.Values.configMaps }}        
        volumeMounts: 
        {{- range $configMap := $.Values.configMaps }}
        - name: {{ $.Values.name }}-config
          mountPath: {{ $configMap.mountPath }}
          subPath: {{ $configMap.name }}        
        {{- end }}
        {{- range .volumeMounts }}
        - name: {{ .name }}
          mountPath: {{ .mountPath }}
        {{- end }}
        {{- end }}
      {{- end }}

      initContainers:
      {{- with $.Values.initContainer }}
      - name: "{{ .name }}"
        image: {{ .dockerRegistry | default $.Values.global.dockerRegistry }}/{{ .image }}:{{ .imageVersion | default $.Values.global.defaultImageVersion }}
        imagePullPolicy: {{ .imagePullPolicy | default $.Values.global.imagePullPolicy }}
        {{- if .command}}
        command: 
        - {{ .command }}
        {{- end -}}
        {{- if .resources }}
        resources:
          {{ toYaml .resources | nindent 10 | trim }}
        {{- else if hasKey $.Values.global "resources" }}
        resources:
          {{ toYaml $.Values.global.resources | nindent 10 | trim }}
        {{- end }}
        {{- if .env }}
        env:
        {{- range $e := .env}}
        - name: {{ $e.name }}
          value: "{{ (tpl ($e.value | toString) $) }}"
        {{ end -}}
        {{ end -}}
        {{- if .args}}
        args:
        {{- range $arg := .args}}
        - {{ $arg }}
        {{- end -}}
        {{- end }}
        {{- if .volumeMounts }}        
        volumeMounts: 
        {{- range .volumeMounts }}
        - name: {{ .name }}
          mountPath: {{ .mountPath }}
        {{- end }}
        {{- end }}
      {{- end -}}

      {{- if $.Values.configMaps }}
      volumes:
      - name: {{ $.Values.name }}-config
        configMap:
          name: {{ $.Values.name }}-{{ $vmId }}
      {{- range $.Values.volumes }}
      - name: {{ .name }}
        emptyDir: {}
      {{- end }}
      {{- end }}
      
      {{- if hasKey $.Values "topologySpreadConstraints" }}
      topologySpreadConstraints:
        {{ tpl $.Values.topologySpreadConstraints . | nindent 6 | trim }}
      {{- else if hasKey $.Values.global  "topologySpreadConstraints" }}
      topologySpreadConstraints:
        {{ tpl $.Values.global.topologySpreadConstraints . | nindent 6 | trim }}
      {{- end }}
      hostname: {{ $.Values.name }}
      restartPolicy: {{ $.Values.restartPolicy | default $.Values.global.restartPolicy}}
{{- end }}
{{- end }}
{{- end }}

{{- if or $.Values.global.hpa.enabled (and $.Values.hpa $.Values.hpa.enabled) }}
{{ include "socialnetwork.templates.baseHPA" . }}
{{- end }}
