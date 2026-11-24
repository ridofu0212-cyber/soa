import { copyFile, mkdir } from "node:fs/promises";

await mkdir("dist/swagger-assets", { recursive: true });
for (const file of ["swagger-ui.css", "swagger-ui-bundle.js", "LICENSE"]) {
  await copyFile("node_modules/swagger-ui-dist/" + file, "dist/swagger-assets/" + file);
}
