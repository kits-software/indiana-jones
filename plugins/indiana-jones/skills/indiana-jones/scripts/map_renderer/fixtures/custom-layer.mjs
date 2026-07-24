function compileShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const message = gl.getShaderInfoLog(shader);
    gl.deleteShader(shader);
    throw new Error(`fixture shader compilation failed: ${message}`);
  }
  return shader;
}

function createLayer() {
  return {
    id: 'fixture-custom-webgl-layer',
    type: 'custom',
    renderingMode: '3d',
    onAdd(_map, gl) {
      /*
       * Draw a fixed diagnostic triangle through MapLibre's own WebGL2
       * context. It proves the custom-layer adapter seam used by a future
       * Three.js/3D Tiles module without introducing network dependencies.
       */

      const vertex = compileShader(
        gl,
        gl.VERTEX_SHADER,
        `#version 300 es
        const vec2 positions[3] = vec2[3](
          vec2(-0.92, 0.92),
          vec2(-0.58, 0.92),
          vec2(-0.92, 0.58)
        );
        void main() {
          gl_Position = vec4(positions[gl_VertexID], 0.0, 1.0);
        }`,
      );
      const fragment = compileShader(
        gl,
        gl.FRAGMENT_SHADER,
        `#version 300 es
        precision highp float;
        out vec4 color;
        void main() {
          color = vec4(0.95, 0.18, 0.12, 1.0);
        }`,
      );
      this.program = gl.createProgram();
      gl.attachShader(this.program, vertex);
      gl.attachShader(this.program, fragment);
      gl.linkProgram(this.program);
      gl.deleteShader(vertex);
      gl.deleteShader(fragment);
      if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) {
        throw new Error(`fixture program link failed: ${gl.getProgramInfoLog(this.program)}`);
      }
      this.vertexArray = gl.createVertexArray();
    },
    render(gl) {
      /*
       * MapLibre may leave per-tile scissor, stencil, viewport, and color-mask
       * state active. Save and restore every state this diagnostic overrides
       * because later custom layers share the same WebGL2 context.
       */

      const capabilities = [
        gl.BLEND,
        gl.CULL_FACE,
        gl.DEPTH_TEST,
        gl.SCISSOR_TEST,
        gl.STENCIL_TEST,
      ];
      const enabled = capabilities.map((capability) => gl.isEnabled(capability));
      const viewport = gl.getParameter(gl.VIEWPORT);
      const colorMask = gl.getParameter(gl.COLOR_WRITEMASK);
      for (const capability of capabilities) {
        gl.disable(capability);
      }
      gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
      gl.colorMask(true, true, true, true);
      gl.useProgram(this.program);
      gl.bindVertexArray(this.vertexArray);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      gl.bindVertexArray(null);
      gl.viewport(...viewport);
      gl.colorMask(...colorMask);
      for (let index = 0; index < capabilities.length; index += 1) {
        if (enabled[index]) {
          gl.enable(capabilities[index]);
        }
      }
    },
    onRemove(_map, gl) {
      gl.deleteVertexArray(this.vertexArray);
      gl.deleteProgram(this.program);
    },
  };
}

export async function install({map}) {
  const layer = createLayer();
  map.addLayer(layer);
  const ready = new Promise((resolvePromise) => {
    map.once('render', resolvePromise);
    map.triggerRepaint();
  });
  return {layerIds: [layer.id], ready};
}
