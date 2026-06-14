// Configuración del frontend. Detecta el entorno automáticamente:
//  - En localhost (Docker) usa la API local.
//  - En cualquier otro host usa la API en la nube (AWS).
(function () {
  var isLocal = ["localhost", "127.0.0.1"].indexOf(location.hostname) !== -1;
  window.TRACKION_CONFIG = {
    API_BASE: isLocal
      ? "http://localhost:8080/trackion"
      : "https://cfvgpefvtc.execute-api.us-east-2.amazonaws.com/trackion",
  };
})();
