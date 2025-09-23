import { Container, getContainer } from "@cloudflare/containers";

export class MyContainer extends Container<Env> {
  defaultPort = 8080; // Port the container is listening on
  sleepAfter = "10m"; // Stop the instance if requests not sent for 10 minutes
}

export default {
  async fetch(request: Request, env: Env) {
    // Always target the default singleton container so binary bodies are proxied untouched
    const containerInstance = getContainer(env.MY_CONTAINER);
    // Pass the request to the container instance on its default port
    return containerInstance.fetch(request);
  },
};
