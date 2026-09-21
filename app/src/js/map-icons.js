function canvasIcon(size, draw) {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, size, size);
  draw(ctx, size);
  return ctx.getImageData(0, 0, size, size);
}

function windmill(ctx, size) {
  ctx.translate(size / 2, size / 2);
  ctx.strokeStyle = "#0c1a14";
  ctx.fillStyle = "#f4fbff";
  ctx.lineWidth = 5;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(0, 4);
  ctx.lineTo(0, size / 2 - 4);
  ctx.stroke();
  ctx.strokeStyle = "#e8f6ff";
  ctx.lineWidth = 2.4;
  ctx.stroke();
  for (let i = 0; i < 3; i += 1) {
    ctx.save();
    ctx.rotate((i * Math.PI * 2) / 3 - 0.4);
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.quadraticCurveTo(10, -14, 2, -size / 2 + 5);
    ctx.quadraticCurveTo(-7, -13, 0, 0);
    ctx.fillStyle = "#f7fcff";
    ctx.fill();
    ctx.strokeStyle = "#8ec8dc";
    ctx.lineWidth = 1.6;
    ctx.stroke();
    ctx.restore();
  }
  ctx.beginPath();
  ctx.arc(0, 0, 4, 0, Math.PI * 2);
  ctx.fillStyle = "#9fd7ea";
  ctx.fill();
}

function substation(ctx, size) {
  const m = 8;
  ctx.fillStyle = "#1d1a10";
  ctx.strokeStyle = "#f2d07a";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.rect(m, m + 6, size - m * 2, size - m * 2 - 4);
  ctx.fill();
  ctx.stroke();
  ctx.strokeStyle = "#ffe29a";
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  ctx.moveTo(size / 2, m + 8);
  ctx.lineTo(size / 2, size - m - 8);
  ctx.moveTo(size / 2, m + 12);
  ctx.lineTo(size / 2 + 10, m + 22);
  ctx.moveTo(size / 2, m + 12);
  ctx.lineTo(size / 2 - 10, m + 22);
  ctx.stroke();
}

function solar(ctx, size) {
  ctx.translate(size / 2, size / 2);
  ctx.fillStyle = "#d6ef7a";
  ctx.strokeStyle = "#f4ffc4";
  ctx.lineWidth = 1.6;
  for (let i = 0; i < 8; i += 1) {
    ctx.save();
    ctx.rotate((i * Math.PI) / 4);
    ctx.beginPath();
    ctx.rect(-2.6, -size / 2 + 7, 5.2, 11);
    ctx.fill();
    ctx.restore();
  }
  ctx.beginPath();
  ctx.arc(0, 0, 7.5, 0, Math.PI * 2);
  ctx.fillStyle = "#f6f3a8";
  ctx.fill();
}

function demand(ctx, size) {
  ctx.strokeStyle = "#ffb089";
  ctx.fillStyle = "#3a241c";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(10, size - 10);
  ctx.lineTo(10, 22);
  ctx.lineTo(22, 14);
  ctx.lineTo(22, 22);
  ctx.lineTo(size - 10, 22);
  ctx.lineTo(size - 10, size - 10);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = "#edb77a";
  ctx.fillRect(16, 28, 8, 10);
  ctx.fillRect(30, 28, 8, 10);
}

function tower(ctx, size) {
  ctx.translate(size / 2, 6);
  ctx.strokeStyle = "#f4e2a8";
  ctx.lineWidth = 2.4;
  ctx.lineJoin = "round";
  ctx.beginPath();
  ctx.moveTo(-10, size - 16);
  ctx.lineTo(0, 4);
  ctx.lineTo(10, size - 16);
  ctx.moveTo(-7, 22);
  ctx.lineTo(7, 22);
  ctx.moveTo(-11, 14);
  ctx.lineTo(11, 14);
  ctx.stroke();
}

function storage(ctx, size) {
  ctx.fillStyle = "#1a2a28";
  ctx.strokeStyle = "#8ee0c8";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.rect(12, 14, size - 24, size - 26);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = "#8ee0c8";
  ctx.fillRect(18, 22, 6, 16);
  ctx.fillRect(28, 22, 6, 16);
  ctx.fillRect(38, 22, 6, 16);
}

function eel(ctx, size) {
  ctx.translate(size / 2, size / 2);
  ctx.rotate(-0.4);
  ctx.fillStyle = "#7dffb2";
  ctx.beginPath();
  ctx.ellipse(0, 0, size / 2 - 10, 8, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(size / 2 - 12, 0);
  ctx.quadraticCurveTo(size / 2 - 2, -10, size / 2 - 6, 0);
  ctx.quadraticCurveTo(size / 2 - 2, 10, size / 2 - 12, 0);
  ctx.fill();
  ctx.fillStyle = "#102018";
  ctx.beginPath();
  ctx.arc(-size / 2 + 16, -2, 2.2, 0, Math.PI * 2);
  ctx.fill();
}

function bird(ctx, size) {
  ctx.translate(size / 2, size / 2);
  ctx.fillStyle = "#d9f6ff";
  ctx.beginPath();
  ctx.ellipse(2, 2, 11, 7, -0.4, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(-2, 0);
  ctx.quadraticCurveTo(-18, -14, 8, -10);
  ctx.quadraticCurveTo(2, -2, 8, 2);
  ctx.fill();
  ctx.fillStyle = "#edb77a";
  ctx.beginPath();
  ctx.moveTo(12, 0);
  ctx.lineTo(20, 2);
  ctx.lineTo(12, 4);
  ctx.fill();
}

function beaver(ctx, size) {
  ctx.fillStyle = "#e6d08a";
  ctx.beginPath();
  ctx.ellipse(size / 2 - 2, size / 2, 13, 10, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.ellipse(size / 2 + 16, size / 2 + 8, 8, 4, 0.4, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#102018";
  ctx.beginPath();
  ctx.arc(size / 2 - 8, size / 2 - 2, 2, 0, Math.PI * 2);
  ctx.fill();
}

function seal(ctx, size) {
  ctx.translate(size / 2, size / 2);
  ctx.fillStyle = "#c5d4f0";
  ctx.beginPath();
  ctx.ellipse(0, 2, 16, 9, -0.3, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(-12, -2, 7, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#102018";
  ctx.beginPath();
  ctx.arc(-14, -3, 1.8, 0, Math.PI * 2);
  ctx.fill();
}

function fish(ctx, size) {
  ctx.translate(size / 2, size / 2);
  ctx.fillStyle = "#6ec8a0";
  ctx.beginPath();
  ctx.ellipse(0, 0, 16, 8, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(14, 0);
  ctx.lineTo(24, -8);
  ctx.lineTo(24, 8);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = "#102018";
  ctx.beginPath();
  ctx.arc(-8, -2, 2, 0, Math.PI * 2);
  ctx.fill();
}

function toad(ctx, size) {
  ctx.fillStyle = "#edb77a";
  ctx.beginPath();
  ctx.ellipse(size / 2, size / 2 + 4, 16, 11, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(size / 2 - 10, size / 2 - 6, 8, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#102018";
  ctx.beginPath();
  ctx.arc(size / 2 - 12, size / 2 - 8, 2, 0, Math.PI * 2);
  ctx.fill();
}

export function addMapIcons(map) {
  const icons = {
    windmill: canvasIcon(64, windmill),
    substation: canvasIcon(64, substation),
    solar: canvasIcon(64, solar),
    demand: canvasIcon(64, demand),
    tower: canvasIcon(64, tower),
    storage: canvasIcon(64, storage),
    eel: canvasIcon(64, eel),
    bird: canvasIcon(64, bird),
    beaver: canvasIcon(64, beaver),
    seal: canvasIcon(64, seal),
    fish: canvasIcon(64, fish),
    toad: canvasIcon(64, toad),
  };
  for (const [name, image] of Object.entries(icons)) {
    if (!map.hasImage(name)) {
      map.addImage(
        name,
        {
          width: image.width,
          height: image.height,
          data: new Uint8Array(image.data),
        },
        { pixelRatio: 2 },
      );
    }
  }
}
