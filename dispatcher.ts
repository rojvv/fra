import { Entry } from "./entry.ts";
import { ENTRY_KEYS } from "./entry_keys.ts";

export interface FRAnalyticsParams {
  threshold?: number;
  timeout?: number;
  log?: boolean;
  include?: (keyof Entry)[];
  exclude?: (keyof Entry)[];
}

export abstract class AnalyticsDispatcher {
  #endpoint: string;
  #threshold: number;
  get thresholdReached() {
    return this.#entries.length >= this.#threshold;
  }

  constructor(endpoint: string, params?: FRAnalyticsParams) {
    if (params?.include && params.exclude) {
      throw new TypeError(
        "The parameters include and exclude cannot be specified together",
      );
    }
    if (params?.include) {
      checkKeys(params.include);
    }
    if (params?.exclude) {
      checkKeys(params.exclude);
    }
    this.#canLog = params?.log ?? true;
    this.#endpoint = endpoint;
    this.#threshold = params?.threshold ?? 10_000;

    const timeout = params?.timeout ?? 10_000;
    this.#interval = setInterval(() => {
      this.#dispatch();
    }, timeout);
  }

  //// LOGGING
  #canLog = false;
  log: (...data: unknown[]) => void = console.error;
  #log(...data: unknown[]) {
    if (this.#canLog) {
      this.log(...data);
    }
  }

  //// DISPATCHER
  async dispatch() {
    if (this.thresholdReached) {
      await this.#dispatch();
    }
  }

  #entries = new Array<Entry>();
  addEntry(entry: Entry) {
    this.#entries.push(entry);
  }

  #dispatching = false;
  #interval: ReturnType<typeof globalThis.setInterval>;
  destroy() {
    clearInterval(this.#interval);
  }
  async #dispatch() {
    if (this.#dispatching || !this.#entries.length) {
      return;
    }
    this.#dispatching = true;
    try {
      const length = this.#entries.length;
      const body = JSON.stringify(this.#entries);
      this.#log("Dispatching", length, length == 1 ? "entry" : "entries");
      const response = await fetch(this.#endpoint, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body,
      });
      if (!response.ok) {
        this.#log(
          "Analytics server returned response with status code ",
          response.status,
        );
      } else {
        this.#entries.splice(0, length);
      }
    } catch (err) {
      this.#log("Error communicating with analytics server:", err);
    } finally {
      this.#dispatching = false;
    }
  }
}

function checkKeys(keys: string[]) {
  for (const key of ENTRY_KEYS) {
    if (!keys.includes(key)) {
      throw new TypeError(`Invalid key: ${key}`);
    }
  }
}
