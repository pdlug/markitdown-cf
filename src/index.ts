import { Container, getRandom } from "@cloudflare/containers";

const INSTANCE_COUNT = 3;

export class MyContainer extends Container<Env> {
  defaultPort = 8080; // Port the container is listening on
  sleepAfter = "10m"; // Stop the instance if requests not sent for 10 minutes
}

export default {
  async fetch(request: Request, env: Env) {
    const containerInstance = await getRandom(env.MY_CONTAINER, INSTANCE_COUNT);
    return containerInstance.fetch(request);
  },
};
