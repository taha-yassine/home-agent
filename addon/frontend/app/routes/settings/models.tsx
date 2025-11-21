import { useEffect, useState } from "react";
import {
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
  Combobox,
  ComboboxButton,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from "@headlessui/react";
import { Check, ChevronDown, AlertCircle } from "lucide-react";
import Loading from "../../components/Loading";
import Breadcrumbs from "../../components/Breadcrumbs";

interface Backend {
  id: number;
  name: string | null;
  url: string;
  api_key: string | null;
  type: string;
}

interface Model {
  id: string;
}

interface ModelConfig {
  role: string;
  backend_id: number;
  model: string;
}

interface ModelConfigMap {
  main: ModelConfig | null;
  document_qa: ModelConfig | null;
}

const backendOptions = [
  { id: "vllm", name: "vLLM" },
  { id: "llama.cpp", name: "llama.cpp" },
  { id: "sglang", name: "SGLang" },
  { id: "ollama", name: "Ollama" },
  { id: "openai", name: "OpenAI-compatible" },
];

const roles = [
  { id: "main", name: "Main", description: "Primary model for conversations and general tasks" },
  { id: "document_qa", name: "Document QA", description: "Model used for document question answering" },
];

export default function SettingsModels() {
  const [backends, setBackends] = useState<Backend[]>([]);
  const [modelConfigs, setModelConfigs] = useState<ModelConfigMap>({
    main: null,
    document_qa: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modelsByBackend, setModelsByBackend] = useState<Record<number, Model[]>>({});
  const [loadingModels, setLoadingModels] = useState<Record<number, boolean>>({});
  const [modelsError, setModelsError] = useState<Record<number, string | null>>({});
  const [queryByRole, setQueryByRole] = useState<Record<string, string>>({});

  const inputClasses =
    "mt-1 block w-full rounded-md border-0 py-1.5 px-3 text-sm/6 ring-1 ring-inset ring-zinc-300 dark:ring-zinc-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-zinc-500";

  async function fetchBackends() {
    try {
      const response = await fetch("api/frontend/backends");
      if (!response.ok) {
        throw new Error("Failed to fetch backends");
      }
      const data = await response.json();
      setBackends(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    }
  }

  async function fetchModelConfigs() {
    try {
      const response = await fetch("api/frontend/model-config");
      if (!response.ok) {
        throw new Error("Failed to fetch model configs");
      }
      const data = await response.json();
      setModelConfigs(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    }
  }

  async function fetchModelsForBackend(backendId: number): Promise<Model[]> {
    if (modelsByBackend[backendId]) {
      return modelsByBackend[backendId]; // Already loaded
    }

    setLoadingModels((prev) => ({ ...prev, [backendId]: true }));
    setModelsError((prev) => ({ ...prev, [backendId]: null }));

    try {
      const response = await fetch(`api/frontend/models?backend_id=${backendId}`);
      if (!response.ok) {
        throw new Error("Failed to fetch models");
      }
      const data = await response.json();
      const models = data.data || [];
      setModelsByBackend((prev) => ({
        ...prev,
        [backendId]: models,
      }));
      return models;
    } catch (err) {
      if (err instanceof Error) {
        setModelsError((prev) => ({ ...prev, [backendId]: err.message }));
      } else {
        setModelsError((prev) => ({ ...prev, [backendId]: "An unknown error occurred" }));
      }
      return [];
    } finally {
      setLoadingModels((prev) => ({ ...prev, [backendId]: false }));
    }
  }

  async function saveModelConfig(role: string, backendId: number, model: string) {
    try {
      const response = await fetch(`api/frontend/model-config/${role}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ backend_id: backendId, model }),
      });
      if (!response.ok) {
        throw new Error("Failed to save model config");
      }
      await fetchModelConfigs();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    }
  }

  useEffect(() => {
    async function load() {
      setLoading(true);
      await Promise.all([fetchBackends(), fetchModelConfigs()]);
      setLoading(false);
    }
    load();
  }, []);

  useEffect(() => {
    // Preload models for configured backends
    Object.values(modelConfigs).forEach((config) => {
      if (config && !modelsByBackend[config.backend_id]) {
        fetchModelsForBackend(config.backend_id);
      }
    });
  }, [modelConfigs]);

  const handleBackendChange = async (role: string, backendId: number) => {
    const models = await fetchModelsForBackend(backendId);
    if (models.length > 0) {
      await saveModelConfig(role, backendId, models[0].id);
    }
  };

  const handleModelChange = (role: string, backendId: number, modelId: string) => {
    saveModelConfig(role, backendId, modelId);
  };

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <>
      <div className="flex justify-between items-center mb-4 min-h-10">
        <Breadcrumbs />
      </div>

      <div className="space-y-6">
        {roles.map((role) => {
          const config = modelConfigs[role.id as keyof ModelConfigMap];
          const selectedBackend = config
            ? backends.find((b) => b.id === config.backend_id)
            : null;
          const models = config ? modelsByBackend[config.backend_id] || [] : [];
          const isLoadingModels = config ? loadingModels[config.backend_id] || false : false;
          const modelError = config ? modelsError[config.backend_id] : null;
          const query = queryByRole[role.id] || "";

          const filteredModels =
            query === ""
              ? models
              : models.filter((model) => {
                  return model.id.toLowerCase().includes(query.toLowerCase());
                });

          return (
            <div
              key={role.id}
              className="border border-zinc-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950 p-6"
            >
              <div className="mb-4">
                <h3 className="text-base font-medium text-zinc-900 dark:text-white">
                  {role.name}
                </h3>
                <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
                  {role.description}
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Backend
                  </label>
                  <Listbox
                    value={selectedBackend}
                    onChange={(backend) => {
                      if (backend) {
                        handleBackendChange(role.id, backend.id);
                      }
                    }}
                  >
                    <ListboxButton
                      className={
                        inputClasses + " relative text-left cursor-pointer w-full"
                      }
                    >
                      <span className="block truncate">
                        {selectedBackend
                          ? selectedBackend.name ||
                            "Unnamed"
                          : "Select a backend"}
                      </span>
                      <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                        <ChevronDown
                          className="h-5 w-5 text-zinc-400"
                          aria-hidden="true"
                        />
                      </span>
                    </ListboxButton>
                    <ListboxOptions
                      transition
                      anchor="bottom"
                      className="z-10 mt-1 w-[var(--button-width)] !max-h-60 overflow-auto rounded-md bg-white dark:bg-zinc-900 p-1 text-base shadow-lg ring-1 ring-zinc-300 dark:ring-zinc-700 focus:outline-none sm:text-sm empty:invisible transition duration-100 ease-in data-leave:data-closed:opacity-0 [--anchor-gap:theme(spacing.1)]"
                    >
                      {backends.map((backend) => (
                        <ListboxOption
                          key={backend.id}
                          value={backend}
                          className="group flex cursor-pointer items-center gap-2 rounded-md py-1.5 px-3 select-none data-focus:bg-zinc-100 dark:data-focus:bg-zinc-800"
                        >
                          <Check
                            className="invisible size-4 text-zinc-600 dark:text-zinc-300 group-data-selected:visible"
                            aria-hidden="true"
                          />
                          <span className="text-sm text-zinc-900 dark:text-zinc-100">
                            {backend.name || "Unnamed"}
                          </span>
                        </ListboxOption>
                      ))}
                    </ListboxOptions>
                  </Listbox>
                </div>

                {selectedBackend && (
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                      Model
                    </label>
                    {isLoadingModels ? (
                      <div className="text-sm text-zinc-500 dark:text-zinc-400">
                        Loading models...
                      </div>
                    ) : modelError ? (
                      <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
                        <AlertCircle className="h-5 w-5" aria-hidden="true" />
                        <span>{modelError}</span>
                      </div>
                    ) : models.length === 0 ? (
                      <div className="text-sm text-zinc-500 dark:text-zinc-400">
                        No models available
                      </div>
                    ) : (
                      <Combobox
                        as="div"
                        value={config?.model || null}
                        onChange={(value: string | null) => {
                          if (value && config) {
                            handleModelChange(role.id, config.backend_id, value);
                          }
                        }}
                        onClose={() => setQueryByRole({ ...queryByRole, [role.id]: "" })}
                      >
                        <div className="relative">
                          <ComboboxInput
                            className="w-full rounded-md border-0 bg-white dark:bg-zinc-950 py-1.5 pl-3 pr-10 text-zinc-900 dark:text-zinc-100 ring-1 ring-inset ring-zinc-300 dark:ring-zinc-700 focus:outline-none sm:text-sm sm:leading-6"
                            onChange={(event) =>
                              setQueryByRole({
                                ...queryByRole,
                                [role.id]: event.target.value,
                              })
                            }
                            displayValue={() => config?.model || ""}
                          />
                          <ComboboxButton className="cursor-pointer group absolute inset-y-0 right-0 flex items-center rounded-r-md px-2 focus:outline-none">
                            <ChevronDown
                              className="h-5 w-5 text-zinc-400 group-data-hover:text-zinc-600"
                              aria-hidden="true"
                            />
                          </ComboboxButton>
                        </div>

                        <ComboboxOptions
                          transition
                          anchor="bottom"
                          className="w-[var(--input-width)] z-10 mt-1 !max-h-60 overflow-auto rounded-md bg-white dark:bg-zinc-900 p-1 text-base shadow-lg ring-1 ring-zinc-300 dark:ring-zinc-700 focus:outline-none sm:text-sm empty:invisible transition duration-100 ease-in data-leave:data-closed:opacity-0 [--anchor-gap:theme(spacing.1)]"
                        >
                          {filteredModels.map((model) => (
                            <ComboboxOption
                              key={model.id}
                              value={model.id}
                              className="group flex cursor-pointer items-center gap-2 rounded-md py-1.5 px-3 select-none data-focus:bg-zinc-100 dark:data-focus:bg-zinc-800"
                            >
                              <Check
                                className="invisible size-4 text-zinc-600 dark:text-zinc-300 group-data-selected:visible"
                                aria-hidden="true"
                              />
                              <span className="text-sm text-zinc-900 dark:text-zinc-100">
                                {model.id}
                              </span>
                            </ComboboxOption>
                          ))}
                        </ComboboxOptions>
                      </Combobox>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

