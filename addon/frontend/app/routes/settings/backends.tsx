import { useEffect, useState } from "react";
import {
  Dialog,
  DialogBackdrop,
  DialogPanel,
  DialogTitle,
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
import { Check, ChevronDown, MoreVertical, Trash2 } from "lucide-react";
import Loading from "../../components/Loading";
import Breadcrumbs from "../../components/Breadcrumbs";

interface Backend {
  id: number;
  name: string | null;
  url: string;
  api_key: string | null;
  type: string;
}

const backendTypes = [
  { id: "vllm", name: "vLLM" },
  { id: "llama.cpp", name: "llama.cpp" },
  { id: "sglang", name: "SGLang" },
  { id: "ollama", name: "Ollama" },
  { id: "openai", name: "OpenAI-compatible" },
];

export default function SettingsBackends() {
  const [backends, setBackends] = useState<Backend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newBackend, setNewBackend] = useState({
    name: "",
    url: "",
    api_key: "",
    type: "vllm",
  });
  const [isAddBackendOpen, setIsAddBackendOpen] = useState(false);

  const inputClasses =
    "mt-1 block w-full rounded-md border-0 py-1.5 px-3 text-sm/6 ring-1 ring-inset ring-zinc-300 dark:ring-zinc-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-zinc-500";

  async function fetchBackends() {
    try {
      setLoading(true);
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
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchBackends();
  }, []);

  const handleDeleteBackend = async (backendId: number) => {
    try {
      const response = await fetch(`api/frontend/backends/${backendId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error("Failed to delete backend");
      }
      await fetchBackends();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    }
  };

  const handleCreateBackend = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch("api/frontend/backends", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newBackend),
      });
      if (!response.ok) {
        throw new Error("Failed to create backend");
      }
      setNewBackend({ name: "", url: "", api_key: "", type: "vllm" });
      await fetchBackends();
      setIsAddBackendOpen(false);
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
          onClick={() => setIsAddBackendOpen(true)}
          className="cursor-pointer inline-flex justify-center rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-zinc-300 focus:ring-offset-2 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900 dark:focus:ring-zinc-700 dark:focus:ring-offset-zinc-950"
        >
          Add Backend
        </button>
      </div>
      <div className="overflow-hidden border border-zinc-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950">
        <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-900">
            <tr>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                Name
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                Type
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
            {backends.map((backend) => (
              <tr key={backend.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-500 dark:text-zinc-400">
                  {backend.name || "Unnamed"}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-500 dark:text-zinc-400">
                  {backendTypes.find((type) => type.id === backend.type)
                    ?.name || backend.type}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-500 dark:text-zinc-400">
                  {backend.url}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-500 dark:text-zinc-400">
                  {backend.api_key}
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
                            onClick={() => handleDeleteBackend(backend.id)}
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
        open={isAddBackendOpen}
        as="div"
        className="relative z-50"
        onClose={() => setIsAddBackendOpen(false)}
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
                Add New Backend
              </DialogTitle>
              <form
                onSubmit={handleCreateBackend}
                className="mt-4"
              >
                <Fieldset className="space-y-4">
                  <Field>
                    <Label
                      htmlFor="name"
                      className="block text-sm font-medium text-zinc-700 dark:text-zinc-300"
                    >
                      Name
                    </Label>
                    <Input
                      type="text"
                      id="name"
                      value={newBackend.name}
                      onChange={(e) =>
                        setNewBackend({
                          ...newBackend,
                          name: e.target.value,
                        })
                      }
                      className={inputClasses}
                      placeholder="My Backend"
                    />
                  </Field>
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
                      value={newBackend.url}
                      onChange={(e) =>
                        setNewBackend({
                          ...newBackend,
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
                      value={newBackend.api_key}
                      onChange={(e) =>
                        setNewBackend({
                          ...newBackend,
                          api_key: e.target.value,
                        })
                      }
                      className={inputClasses}
                    />
                  </Field>
                  <Field>
                    <Label
                      htmlFor="type"
                      className="block text-sm font-medium text-zinc-700 dark:text-zinc-300"
                    >
                      Backend Type
                    </Label>
                    <Listbox
                      value={newBackend.type}
                      onChange={(value) =>
                        setNewBackend({ ...newBackend, type: value })
                      }
                    >
                      <ListboxButton
                        className={
                          inputClasses + " relative text-left cursor-pointer"
                        }
                      >
                        <span className="block truncate">
                          {
                            backendTypes.find((type) => type.id === newBackend.type)?.name
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
                        {backendTypes.map((type) => (
                          <ListboxOption
                            key={type.id}
                            value={type.id}
                            className="group flex cursor-pointer items-center gap-2 rounded-md py-1.5 px-3 select-none data-focus:bg-zinc-100 dark:data-focus:bg-zinc-800"
                          >
                            <Check
                              className="invisible size-4 text-zinc-600 dark:text-zinc-300 group-data-selected:visible"
                              aria-hidden="true"
                            />
                            <span className="text-sm/6 text-zinc-900 dark:text-zinc-100">
                              {type.name}
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
                    onClick={() => setIsAddBackendOpen(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="cursor-pointer inline-flex justify-center rounded-md border border-transparent bg-zinc-800 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-500 focus:ring-offset-2 dark:bg-zinc-200 dark:text-zinc-900 dark:hover:bg-zinc-300"
                  >
                    Add Backend
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

