import { useEffect, useState, Fragment } from "react";
import {
  Dialog,
  DialogBackdrop,
  DialogPanel,
  DialogTitle,
  Combobox,
  ComboboxButton,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
  Fieldset,
  Field,
  Label,
  Input,
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
  Menu,
  MenuButton,
  MenuItem,
  MenuItems,
} from "@headlessui/react";
import { Check, ChevronDown, MoreVertical, Trash2, AlertCircle } from "lucide-react";
import Loading from "../../components/Loading";
import Breadcrumbs from "../../components/Breadcrumbs";

interface Connection {
  id: number;
  url: string;
  api_key: string | null;
  backend: string;
  model: string | null;
  is_active: boolean;
}

interface Model {
  id: string;
}

const backendOptions = [
  { id: "vllm", name: "vLLM" },
  { id: "llama.cpp", name: "llama.cpp" },
  { id: "sglang", name: "SGLang" },
  { id: "ollama", name: "Ollama" },
  { id: "openai", name: "OpenAI-compatible" },
];

export default function ConnectionsLlm() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConnection, setSelectedConnection] = useState<Connection | null>(
    null
  );
  const [newConnection, setNewConnection] = useState({
    url: "",
    api_key: "",
    backend: "vllm",
  });
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [isAddConnectionOpen, setIsAddConnectionOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [modelsError, setModelsError] = useState<string | null>(null);

  const inputClasses =
    "mt-1 block w-full rounded-md border-0 py-1.5 px-3 text-sm/6 ring-1 ring-inset ring-zinc-300 dark:ring-zinc-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-zinc-500";

  async function fetchConnections() {
    try {
      setLoading(true);
      const response = await fetch("/api/frontend/connections");
      if (!response.ok) {
        throw new Error("Failed to fetch connections");
      }
      const data = await response.json();
      setConnections(data);
      const activeConnection = data.find((c: Connection) => c.is_active);
      if (activeConnection) {
        setSelectedConnection(activeConnection);
        if (activeConnection.model) {
          setSelectedModel({ id: activeConnection.model });
        }
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    } finally {
      setLoading(false);
    }
  }

  async function fetchModels() {
    if (!selectedConnection) return;
    try {
      setModelsError(null);
      const response = await fetch("/api/frontend/models");
      if (!response.ok) {
        throw new Error("Failed to fetch models");
      }
      const data = await response.json();
      setModels(data.data);
      setModelsError(null);
    } catch (err) {
      if (err instanceof Error) {
        setModelsError(err.message);
      } else {
        setModelsError("An unknown error occurred");
      }
    }
  }

  useEffect(() => {
    fetchConnections();
  }, []);

  useEffect(() => {
    if (selectedConnection) {
      fetchModels();
      if (selectedConnection.model) {
        setSelectedModel({ id: selectedConnection.model });
      } else {
        setSelectedModel(null);
      }
    }
  }, [selectedConnection]);

  const filteredModels =
    query === ""
      ? models
      : models.filter((model) => {
          return model.id.toLowerCase().includes(query.toLowerCase());
        });

  const handleModelChange = (value: Model | string | null) => {
    let modelId: string;
    if (typeof value === "string") {
      modelId = value;
      setSelectedModel({ id: modelId });
    } else if (value) {
      modelId = value.id;
      setSelectedModel(value);
    } else {
      setSelectedModel(null);
      return;
    }
    handleSaveModel(modelId);
  };

  const handleSetActive = async (connection: Connection) => {
    try {
      const response = await fetch(
        `/api/frontend/connections/${connection.id}/active`,
        {
          method: "PUT",
        }
      );
      if (!response.ok) {
        throw new Error("Failed to set active connection");
      }
      await fetchConnections();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    }
  };

  const handleSaveModel = async (modelId: string) => {
    if (!selectedConnection) return;
    try {
      const response = await fetch(
        `/api/frontend/connections/${selectedConnection.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ model: modelId }),
        }
      );
      if (!response.ok) {
        throw new Error("Failed to save model");
      }
      await fetchConnections();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    }
  };

  const handleDeleteConnection = async (connectionId: number) => {
    try {
      const response = await fetch(`/api/frontend/connections/${connectionId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error("Failed to delete connection");
      }
      await fetchConnections();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    }
  };

  const handleCreateConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch("/api/frontend/connections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newConnection),
      });
      if (!response.ok) {
        throw new Error("Failed to create connection");
      }
      setNewConnection({ url: "", api_key: "", backend: "vllm" });
      await fetchConnections();
      setIsAddConnectionOpen(false);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    }
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
        <button
          onClick={() => setIsAddConnectionOpen(true)}
          className="cursor-pointer inline-flex justify-center rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-zinc-300 focus:ring-offset-2 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900 dark:focus:ring-zinc-700 dark:focus:ring-offset-zinc-950"
        >
          Add Connection
        </button>
      </div>
      {/* TODO: Find a way to reconcile overflow-hidden and the dropdown menu */}
      <div className="overflow-hidden border border-zinc-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950">
        <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-900">
            <tr>
              <th scope="col" className="w-12"></th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                Backend
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                Model
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                URL
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                API Key
              </th>
              <th scope="col" className="relative px-6 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800 bg-white dark:bg-zinc-950">
            {connections.map((connection) => (
              <tr key={connection.id}>
                <td className="pl-4 py-4">
                  <input
                    type="radio"
                    name="active_connection"
                    checked={connection.is_active}
                    onChange={() => handleSetActive(connection)}
                    className="cursor-pointer h-4 w-4 border-zinc-300 bg-zinc-100 text-zinc-900 focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-700 dark:focus:ring-offset-zinc-950"
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-500 dark:text-zinc-400">
                  {backendOptions.find((b) => b.id === connection.backend)
                    ?.name || connection.backend}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-500 dark:text-zinc-400">
                  {connection.is_active ? (
                    modelsError ? (
                      <div className="flex items-center gap-2">
                        <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" aria-hidden="true" />
                        <span className="text-sm text-red-600 dark:text-red-400">{modelsError}</span>
                      </div>
                    ) : (
                      <Combobox
                        as="div"
                        value={selectedModel}
                        onChange={handleModelChange}
                        onClose={() => setQuery("")}
                      >
                        <div className="relative">
                          <ComboboxInput
                            className="w-full rounded-md border-0 bg-white dark:bg-zinc-950 py-1.5 pl-3 pr-10 text-zinc-900 dark:text-zinc-100 ring-1 ring-inset ring-zinc-300 dark:ring-zinc-700 focus:outline-none sm:text-sm sm:leading-6"
                            onChange={(event) => setQuery(event.target.value)}
                            displayValue={(model: Model) => model?.id || ""}
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
                              value={model}
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
                    )
                  ) : (
                    <span>{connection.model || "N/A"}</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-500 dark:text-zinc-400">
                  {connection.url}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-500 dark:text-zinc-400">
                  {connection.api_key}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <Menu as="div" className="relative inline-block text-left">
                    <div>
                      <MenuButton className="cursor-pointer inline-flex w-full justify-center rounded-md p-2 text-sm font-medium text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-white/75">
                        <MoreVertical className="h-5 w-5" aria-hidden="true" />
                      </MenuButton>
                    </div>
                    <MenuItems
                      transition
                      className="absolute right-0 mt-2 w-32 origin-top-right divide-y divide-zinc-100 rounded-md bg-white dark:bg-zinc-900 shadow-lg ring-1 ring-black/5 focus:outline-none transition data-[closed]:scale-95 data-[closed]:opacity-0"
                      anchor="bottom end"
                    >
                      <div className="px-1 py-1">
                        <MenuItem>
                          <button
                            onClick={() => handleDeleteConnection(connection.id)}
                            className="group flex w-full items-center rounded-md px-2 py-2 text-sm cursor-pointer text-red-700 dark:text-red-400 data-[focus]:bg-zinc-100 dark:data-[focus]:bg-zinc-800 data-[focus]:text-red-900 dark:data-[focus]:text-red-200"
                          >
                            <Trash2 className="mr-2 h-5 w-5" aria-hidden="true" />
                            Delete
                          </button>
                        </MenuItem>
                      </div>
                    </MenuItems>
                  </Menu>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Dialog
        open={isAddConnectionOpen}
        as="div"
        className="relative z-50"
        onClose={() => setIsAddConnectionOpen(false)}
      >
        <DialogBackdrop
          transition
          className="fixed inset-0 bg-black/30 transition-opacity duration-300 ease-out data-[closed]:opacity-0"
        />
        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <DialogPanel
              transition
              className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-zinc-900 p-6 text-left align-middle shadow-xl transition-all data-[closed]:-translate-y-4 data-[closed]:opacity-0"
            >
              <DialogTitle
                as="h3"
                className="text-lg font-medium leading-6 text-zinc-900 dark:text-zinc-100"
              >
                Add New Connection
              </DialogTitle>
              <form
                onSubmit={handleCreateConnection}
                className="mt-4"
              >
                <Fieldset className="space-y-4">
                  <Field>
                    <Label
                      htmlFor="url"
                      className="block text-sm font-medium text-zinc-700 dark:text-zinc-300"
                    >
                      URL
                    </Label>
                    <Input
                      type="url"
                      id="url"
                      value={newConnection.url}
                      onChange={(e) =>
                        setNewConnection({
                          ...newConnection,
                          url: e.target.value,
                        })
                      }
                      className={inputClasses}
                      required
                    />
                  </Field>
                  <Field>
                    <Label
                      htmlFor="api_key"
                      className="block text-sm font-medium text-zinc-700 dark:text-zinc-300"
                    >
                      API Key
                    </Label>
                    <Input
                      type="password"
                      id="api_key"
                      value={newConnection.api_key}
                      onChange={(e) =>
                        setNewConnection({
                          ...newConnection,
                          api_key: e.target.value,
                        })
                      }
                      className={inputClasses}
                    />
                  </Field>
                  <Field>
                    <Label
                      htmlFor="backend"
                      className="block text-sm font-medium text-zinc-700 dark:text-zinc-300"
                    >
                      Backend
                    </Label>
                    <Listbox
                      value={newConnection.backend}
                      onChange={(value) =>
                        setNewConnection({ ...newConnection, backend: value })
                      }
                    >
                      <ListboxButton
                        className={
                          inputClasses + " relative text-left cursor-pointer"
                        }
                      >
                        <span className="block truncate">
                          {
                            backendOptions.find(
                              (o) => o.id === newConnection.backend
                            )?.name
                          }
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
                        {backendOptions.map((option) => (
                          <ListboxOption
                            key={option.id}
                            value={option.id}
                            className="group flex cursor-pointer items-center gap-2 rounded-md py-1.5 px-3 select-none data-focus:bg-zinc-100 dark:data-focus:bg-zinc-800"
                          >
                            <Check
                              className="invisible size-4 text-zinc-600 dark:text-zinc-300 group-data-selected:visible"
                              aria-hidden="true"
                            />
                            <span className="text-sm/6 text-zinc-900 dark:text-zinc-100">
                              {option.name}
                            </span>
                          </ListboxOption>
                        ))}
                      </ListboxOptions>
                    </Listbox>
                  </Field>
                </Fieldset>
                <div className="mt-6 flex justify-end gap-4">
                  <button
                    type="button"
                    className="cursor-pointer inline-flex justify-center rounded-md border border-zinc-300 dark:border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-500 focus-visible:ring-offset-2"
                    onClick={() => setIsAddConnectionOpen(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="cursor-pointer inline-flex justify-center rounded-md border border-transparent bg-zinc-800 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-500 focus:ring-offset-2 dark:bg-zinc-200 dark:text-zinc-900 dark:hover:bg-zinc-300"
                  >
                    Add Connection
                  </button>
                </div>
              </form>
            </DialogPanel>
          </div>
        </div>
      </Dialog>
    </>
  );
} 