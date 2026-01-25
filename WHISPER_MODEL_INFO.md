# Whisper Model Information

## About the Whisper Model

### Model Location

The Whisper model is **NOT stored in the project directory**. It's downloaded and cached by the `openai-whisper` library on first use.

**Cache Location**: `~/.cache/whisper/`

On your system, the model is stored at:
```
/Users/damithomas/.cache/whisper/base.pt
```

**Size**: ~139 MB (for "base" model)

### Model Download

- **First Run**: When you first use Whisper, it automatically downloads the model
- **Subsequent Runs**: The cached model is reused (no download needed)
- **Internet Required**: Only needed for the first download

### Model Sizes Available

The `openai-whisper` library supports multiple model sizes:

- `tiny` - ~39 MB (fastest, least accurate)
- `base` - ~139 MB (balanced, default)
- `small` - ~466 MB (better accuracy)
- `medium` - ~1.4 GB (high accuracy)
- `large` - ~2.9 GB (best accuracy, slowest)

**Current Configuration**: `base` (set in `pi/config.py`)

### How It Works in Tests

1. **First Test Run**:
   ```python
   transcriber = WhisperTranscriber()  # Uses "base" model
   transcriber.load_model()  # Downloads model if not cached
   ```

2. **Subsequent Runs**:
   - Model is loaded from cache (`~/.cache/whisper/base.pt`)
   - No download needed
   - Faster startup

3. **In Tests**:
   - Each test that uses Whisper loads the model
   - Model stays in memory during test execution
   - Can be unloaded to free memory

### Model Files in Project

**No model files are in the project directory** - this is intentional:
- Models are large (139MB+)
- Would bloat the repository
- Automatically downloaded when needed
- Cached locally for reuse

### Checking Model Status

To see if the model is downloaded:

```bash
ls -lh ~/.cache/whisper/
```

You should see files like:
- `base.pt` - The model weights
- `base.pt.timestamp` - Download timestamp

### Changing Model Size

To use a different model size, edit `pi/config.py`:

```python
WHISPER_MODEL_SIZE = "small"  # or "tiny", "medium", "large"
```

**Note**: Larger models are more accurate but slower. For real-time use, "base" or "small" are recommended.

### Troubleshooting

**Model won't download**:
- Check internet connection
- Check disk space (models need ~500MB free)
- Check write permissions to `~/.cache/whisper/`

**Model takes too long to load**:
- First load downloads the model (can take 1-2 minutes)
- Subsequent loads are faster (just loading from disk)
- Consider using "tiny" model for faster testing

**Model not found**:
- Delete `~/.cache/whisper/` and let it re-download
- Check that `openai-whisper` is installed: `pip list | grep whisper`
