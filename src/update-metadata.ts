import { DictionaryIndex } from 'yomichan-dict-builder';

export interface UpdateMetadata {
  isUpdatable?: boolean;
  indexUrl?: string;
  downloadUrl?: string;
}

/**
 * Adds Yomitan's remote update fields only when a dictionary is explicitly
 * configured for publishing.
 */
export function applyUpdateMetadata<T extends UpdateMetadata>(
  index: DictionaryIndex,
  config: T,
): DictionaryIndex {
  if (!config.isUpdatable) {
    if (config.indexUrl || config.downloadUrl) {
      throw new Error(
        'indexUrl/downloadUrl 已填写，但 isUpdatable 不是 true',
      );
    }
    return index;
  }

  if (!config.indexUrl || !config.downloadUrl) {
    throw new Error(
      '启用 isUpdatable 时必须同时填写 indexUrl 和 downloadUrl',
    );
  }

  return index
    .setIsUpdatable(true)
    .setIndexUrl(config.indexUrl)
    .setDownloadUrl(config.downloadUrl);
}
